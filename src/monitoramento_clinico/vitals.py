"""Ingestão incremental e alertas persistentes por regras sintéticas."""

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any, Literal, Self
from uuid import uuid4

from pydantic import Field, model_validator

from monitoramento_clinico.contracts import (
    Alert,
    Contract,
    Event,
    Evidence,
    Measurement,
    Session,
)


class VitalsConfig(Contract):
    version: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    persistence_seconds: float = Field(gt=0)
    max_gap_seconds: float = Field(gt=0)
    limits: dict[str, tuple[float, float]]

    @model_validator(mode="after")
    def complete_limits(self) -> Self:
        if set(self.limits) != {"heart_rate", "systolic", "diastolic", "spo2"}:
            raise ValueError("all four signals require limits")
        if any(low >= high for low, high in self.limits.values()):
            raise ValueError("limits must be ordered")
        return self

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(
            json.dumps(self.model_dump(), sort_keys=True).encode()
        ).hexdigest()[:16]


class ProcessingResult(Contract):
    status: Literal["accepted", "duplicate", "out_of_order", "quality_issue"]
    alerts: list[Alert] = Field(default_factory=list)
    processing_ms: float = Field(ge=0)


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS monitoring_sessions (
    session_id TEXT PRIMARY KEY, patient_id TEXT NOT NULL, payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS monitoring_samples (
    session_id TEXT NOT NULL REFERENCES monitoring_sessions(session_id),
    record_id TEXT NOT NULL, payload TEXT NOT NULL, received_at TEXT NOT NULL,
    status TEXT NOT NULL, PRIMARY KEY(session_id, record_id)
);
CREATE TABLE IF NOT EXISTS detector_state (
    session_id TEXT NOT NULL REFERENCES monitoring_sessions(session_id),
    signal TEXT NOT NULL, config TEXT NOT NULL, payload TEXT NOT NULL,
    PRIMARY KEY(session_id, signal, config)
);
CREATE TABLE IF NOT EXISTS monitoring_events (
    event_id TEXT PRIMARY KEY, payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS monitoring_alerts (
    alert_id TEXT PRIMARY KEY, deduplication_key TEXT NOT NULL UNIQUE,
    payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS alert_history (
    history_id INTEGER PRIMARY KEY, alert_id TEXT NOT NULL
        REFERENCES monitoring_alerts(alert_id),
    actor TEXT NOT NULL, occurred_at TEXT NOT NULL,
    action TEXT NOT NULL, comment TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS monitoring_runs (
    run_id TEXT PRIMARY KEY, payload TEXT NOT NULL
);
"""


class VitalsMonitor:
    """Estado e alertas atômicos em SQLite, separados do contexto clínico anterior."""

    def __init__(self, path: Path, config: VitalsConfig) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.config = config
        connection = self._connect()
        try:
            with connection:
                connection.executescript(SCHEMA)
        finally:
            connection.close()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def start_run(
        self, session: Session, speed: float, samples: int, source_id: str | None = None
    ) -> str:
        run_id = str(uuid4())
        payload = {
            "run_id": run_id,
            "patient_id": session.patient_id,
            "session_id": session.session_id,
            "source_id": source_id,
            "started_at": datetime.now(UTC).isoformat(),
            "finished_at": None,
            "status": "running",
            "speed": speed,
            "samples_requested": samples,
            "config_fingerprint": self.config.fingerprint,
            "summary": None,
        }
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    "INSERT INTO monitoring_runs VALUES (?, ?)",
                    (run_id, json.dumps(payload)),
                )
        finally:
            connection.close()
        return run_id

    def finish_run(
        self, run_id: str, summary: dict[str, Any] | None, error: str | None = None
    ) -> None:
        connection = self._connect()
        try:
            with connection:
                row = connection.execute(
                    "SELECT payload FROM monitoring_runs WHERE run_id = ?", (run_id,)
                ).fetchone()
                if row is None:
                    raise ValueError("unknown run")
                payload = json.loads(row["payload"])
                payload.update(
                    finished_at=datetime.now(UTC).isoformat(),
                    status="failed" if error else "completed",
                    summary=summary,
                    error=error,
                )
                connection.execute(
                    "UPDATE monitoring_runs SET payload = ? WHERE run_id = ?",
                    (json.dumps(payload), run_id),
                )
        finally:
            connection.close()

    def register_session(self, session: Session) -> None:
        connection = self._connect()
        try:
            with connection:
                existing = connection.execute(
                    "SELECT payload FROM monitoring_sessions WHERE session_id = ?",
                    (session.session_id,),
                ).fetchone()
                if existing and existing["payload"] != session.model_dump_json():
                    raise ValueError("session identity or interval conflict")
                connection.execute(
                    "INSERT OR IGNORE INTO monitoring_sessions VALUES (?, ?, ?)",
                    (session.session_id, session.patient_id, session.model_dump_json()),
                )
        finally:
            connection.close()

    def process(self, sample: Measurement) -> ProcessingResult:
        started = perf_counter()
        received_at = datetime.now(UTC).isoformat()
        connection = self._connect()
        alerts: list[Alert] = []
        status: Literal["accepted", "duplicate", "out_of_order", "quality_issue"]
        try:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT payload FROM monitoring_sessions WHERE session_id = ?",
                    (sample.session_id,),
                ).fetchone()
                if row is None:
                    raise ValueError("unknown session")
                session = Session.model_validate_json(row["payload"])
                if session.patient_id != sample.patient_id:
                    raise ValueError("patient does not own session")
                if not session.started_at <= sample.occurred_at <= session.ended_at:
                    raise ValueError("sample outside session")
                previous = connection.execute(
                    "SELECT payload FROM monitoring_samples "
                    "WHERE session_id = ? AND record_id = ?",
                    (sample.session_id, sample.record_id),
                ).fetchone()
                if previous:
                    if previous["payload"] != sample.model_dump_json():
                        raise ValueError("record identifier conflict")
                    status = "duplicate"
                else:
                    status, alerts = self._detect(connection, session, sample)
                    connection.execute(
                        "INSERT INTO monitoring_samples VALUES (?, ?, ?, ?, ?)",
                        (
                            sample.session_id,
                            sample.record_id,
                            sample.model_dump_json(),
                            received_at,
                            status,
                        ),
                    )
        finally:
            connection.close()
        return ProcessingResult(
            status=status,
            alerts=alerts,
            processing_ms=(perf_counter() - started) * 1000,
        )

    def _detect(
        self, connection: sqlite3.Connection, session: Session, sample: Measurement
    ) -> tuple[Literal["accepted", "out_of_order", "quality_issue"], list[Alert]]:
        key = (sample.session_id, sample.signal, self.config.fingerprint)
        row = connection.execute(
            "SELECT payload FROM detector_state "
            "WHERE session_id = ? AND signal = ? AND config = ?",
            key,
        ).fetchone()
        state: dict[str, Any] = json.loads(row["payload"]) if row else {}
        last = datetime.fromisoformat(state["last"]) if state else None
        if last is not None and sample.occurred_at <= last:
            return "out_of_order", []
        low, high = self.config.limits[sample.signal]
        direction = (
            "low" if sample.value < low else "high" if sample.value > high else None
        )
        gap = last is None or (sample.occurred_at - last).total_seconds() > (
            self.config.max_gap_seconds
        )
        if sample.quality != "valid" or direction is None:
            state = {}
        elif gap or state.get("direction") != direction:
            state = {
                "onset": sample.occurred_at.isoformat(),
                "direction": direction,
                "first_record": sample.record_id,
                "fired": False,
            }
        state["last"] = sample.occurred_at.isoformat()
        alerts: list[Alert] = []
        if "onset" in state and not state["fired"]:
            onset = datetime.fromisoformat(state["onset"])
            if (
                sample.occurred_at - onset
            ).total_seconds() >= self.config.persistence_seconds:
                identifier = hashlib.sha256(
                    json.dumps(
                        [*key, sample.patient_id, state["onset"], direction]
                    ).encode()
                ).hexdigest()
                event = Event(
                    event_id=f"event-{identifier}",
                    patient_id=sample.patient_id,
                    session_id=sample.session_id,
                    event_type="persistent_deviation",
                    occurred_at=onset,
                    ended_at=sample.occurred_at,
                    processed_at=datetime.now(UTC),
                    detector_version=self.config.version,
                    evidence=[
                        Evidence(
                            source_id=sample.record_id,
                            modality="vitals",
                            start_seconds=(onset - session.started_at).total_seconds(),
                            end_seconds=(
                                sample.occurred_at - session.started_at
                            ).total_seconds(),
                            description=f"{sample.signal}: {sample.value} "
                            f"{sample.unit}; "
                            f"{direction}; synthetic limits [{low}, {high}]; "
                            f"first record {state['first_record']}",
                        )
                    ],
                )
                alert = Alert(
                    alert_id=f"alert-{identifier}",
                    deduplication_key=identifier,
                    patient_id=sample.patient_id,
                    session_id=sample.session_id,
                    event_ids=[event.event_id],
                    emitted_at=datetime.now(UTC),
                    severity="attention",
                )
                connection.execute(
                    "INSERT INTO monitoring_events VALUES (?, ?)",
                    (event.event_id, event.model_dump_json()),
                )
                connection.execute(
                    "INSERT INTO monitoring_alerts VALUES (?, ?, ?)",
                    (alert.alert_id, identifier, alert.model_dump_json()),
                )
                state["fired"] = True
                alerts.append(alert)
        connection.execute(
            "INSERT OR REPLACE INTO detector_state VALUES (?, ?, ?, ?)",
            (*key, json.dumps(state)),
        )
        return ("quality_issue" if sample.quality != "valid" else "accepted"), alerts

    def snapshot(self) -> dict[str, Any]:
        connection = self._connect()
        try:
            return {
                "samples": [
                    dict(row)
                    for row in connection.execute(
                        "SELECT session_id, record_id, status, received_at "
                        "FROM monitoring_samples ORDER BY rowid"
                    )
                ],
                "events": [
                    json.loads(row[0])
                    for row in connection.execute(
                        "SELECT payload FROM monitoring_events ORDER BY rowid"
                    )
                ],
                "alerts": [
                    json.loads(row[0])
                    for row in connection.execute(
                        "SELECT payload FROM monitoring_alerts ORDER BY rowid"
                    )
                ],
                "history": [
                    dict(row)
                    for row in connection.execute(
                        "SELECT * FROM alert_history ORDER BY history_id"
                    )
                ],
                "runs": [
                    json.loads(row[0])
                    for row in connection.execute(
                        "SELECT payload FROM monitoring_runs ORDER BY rowid DESC"
                    )
                ],
            }
        finally:
            connection.close()

    def review_alert(
        self,
        alert_id: str,
        action: Literal["acknowledge", "close"],
        actor: str,
        comment: str,
        review: Literal["confirmed", "false_positive", "inconclusive"] | None = None,
    ) -> Alert:
        if not actor.strip() or not comment.strip():
            raise ValueError("actor and comment required")
        if action not in {"acknowledge", "close"}:
            raise ValueError("unsupported action")
        connection = self._connect()
        try:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT payload FROM monitoring_alerts WHERE alert_id = ?",
                    (alert_id,),
                ).fetchone()
                if row is None:
                    raise ValueError("unknown alert")
                alert = Alert.model_validate_json(row["payload"])
                if (
                    action == "acknowledge"
                    and alert.status == "open"
                    and review is None
                ):
                    updated = Alert.model_validate(
                        {**alert.model_dump(), "status": "acknowledged"}
                    )
                elif (
                    action == "close"
                    and alert.status == "acknowledged"
                    and review is not None
                ):
                    updated = Alert.model_validate(
                        {**alert.model_dump(), "status": "closed", "review": review}
                    )
                else:
                    raise ValueError("invalid alert transition")
                connection.execute(
                    "UPDATE monitoring_alerts SET payload = ? WHERE alert_id = ?",
                    (updated.model_dump_json(), alert_id),
                )
                connection.execute(
                    "INSERT INTO alert_history "
                    "(alert_id, actor, occurred_at, action, comment) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (alert_id, actor, datetime.now(UTC).isoformat(), action, comment),
                )
                return updated
        finally:
            connection.close()
