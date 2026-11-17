"""Prescrições sintéticas e fusão temporal persistente; sem recomendar condutas."""

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from pydantic import Field

from monitoramento_clinico.contracts import (
    Alert,
    Contract,
    Event,
    Evidence,
    Measurement,
    PrescriptionVersion,
)
from monitoramento_clinico.vitals import ProcessingResult, VitalsConfig, VitalsMonitor


class ClinicalConfig(Contract):
    version: str = "synthetic-clinical-v2"
    fusion_window_seconds: float = Field(default=30, gt=0)
    unexpected_dose_ratio: float = Field(default=2, gt=1)
    fusion_event_types: list[str] = Field(
        default_factory=lambda: [
            "persistent_deviation",
            "trend_deviation",
            "critical_mention",
            "unexpected_prescription_change",
            "unexpected_prescription_stop",
            # Legacy synthetic event; retained for persisted config compatibility.
            "long_pause",
            # long_pause_observed has no reference and remains observation-only.
            "pause_change",
            "asymmetry",
            "interruption",
            "rise_candidate",
            "activity_change",
        ]
    )

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(self.model_dump_json().encode()).hexdigest()[:16]


EXTRA_SCHEMA = """
CREATE TABLE IF NOT EXISTS clinical_configuration (
 singleton INTEGER PRIMARY KEY CHECK(singleton = 1), payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS prescription_versions (
 session_id TEXT NOT NULL REFERENCES monitoring_sessions(session_id),
 record_id TEXT NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL,
 PRIMARY KEY(session_id, record_id)
);
CREATE TABLE IF NOT EXISTS modality_availability (
 session_id TEXT NOT NULL REFERENCES monitoring_sessions(session_id),
 modality TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(session_id, modality)
);
CREATE TABLE IF NOT EXISTS event_provenance (
 event_id TEXT PRIMARY KEY REFERENCES monitoring_events(event_id), payload TEXT NOT NULL
);
"""


class ClinicalMonitor(VitalsMonitor):
    def __init__(
        self, path: Path, vitals: VitalsConfig, config: ClinicalConfig | None = None
    ) -> None:
        super().__init__(path, vitals)
        self.clinical_config = config or ClinicalConfig()
        connection = self._connect()
        try:
            connection.executescript(EXTRA_SCHEMA)
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT payload FROM clinical_configuration WHERE singleton = 1"
                ).fetchone()
                payload = self.clinical_config.model_dump_json()
                if row and row[0] != payload:
                    raise ValueError("clinical config changed; use a separate database")
                connection.execute(
                    "INSERT OR IGNORE INTO clinical_configuration VALUES (1, ?)",
                    (payload,),
                )
        finally:
            connection.close()

    def _session(
        self,
        connection: sqlite3.Connection,
        patient: str,
        session: str,
        begin: datetime,
        end: datetime,
    ) -> dict[str, Any]:
        row = connection.execute(
            "SELECT payload FROM monitoring_sessions WHERE session_id = ?", (session,)
        ).fetchone()
        if row is None:
            raise ValueError("unknown session")
        payload: dict[str, Any] = json.loads(row[0])
        if payload["patient_id"] != patient:
            raise ValueError("patient does not own session")
        if (
            not datetime.fromisoformat(payload["started_at"])
            <= begin
            <= end
            <= datetime.fromisoformat(payload["ended_at"])
        ):
            raise ValueError("event outside session")
        return payload

    def _alert(
        self, connection: sqlite3.Connection, events: list[Event]
    ) -> Alert | None:
        ids = sorted(event.event_id for event in events)
        key = hashlib.sha256(
            json.dumps([self.clinical_config.fingerprint, ids]).encode()
        ).hexdigest()
        alert = Alert(
            alert_id=f"clinical-{key}",
            deduplication_key=key,
            patient_id=events[0].patient_id,
            session_id=events[0].session_id,
            event_ids=ids,
            emitted_at=datetime.now(UTC),
            severity="priority"
            if len(events) > 1
            else (
                "attention"
                if events[0].event_type in self.clinical_config.fusion_event_types
                else "observation"
            ),
        )
        cursor = connection.execute(
            "INSERT OR IGNORE INTO monitoring_alerts VALUES (?, ?, ?)",
            (alert.alert_id, key, alert.model_dump_json()),
        )
        return alert if cursor.rowcount else None

    @staticmethod
    def _families(event: Event) -> set[str]:
        # Voice/text and posture/movement are dependent views, not independent sensors.
        groups = {
            "audio": "voice",
            "text": "voice",
            "video": "visual",
            "movement": "visual",
        }
        return {groups.get(e.modality, e.modality) for e in event.evidence}

    def _correlate(self, connection: sqlite3.Connection, event: Event) -> list[Alert]:
        alerts: list[Alert] = []
        if event.event_type not in self.clinical_config.fusion_event_types:
            return alerts
        compatible = [event]
        for row in connection.execute("SELECT payload FROM monitoring_events"):
            other = Event.model_validate_json(row[0])
            if other.event_type not in self.clinical_config.fusion_event_types:
                continue
            if other.event_id == event.event_id or (
                other.patient_id,
                other.session_id,
            ) != (event.patient_id, event.session_id):
                continue
            if not self._families(event).isdisjoint(self._families(other)):
                continue
            if (
                abs((other.occurred_at - event.occurred_at).total_seconds())
                > self.clinical_config.fusion_window_seconds
            ):
                continue
            compatible.append(other)
        if len(compatible) < 2:
            return []
        ids = {e.event_id for e in compatible}
        for row in connection.execute("SELECT payload FROM monitoring_alerts"):
            existing = Alert.model_validate_json(row[0])
            if (existing.patient_id, existing.session_id) != (
                event.patient_id,
                event.session_id,
            ):
                continue
            if len(existing.event_ids) < 2 or not ids.intersection(existing.event_ids):
                continue
            if ids.issubset(existing.event_ids):
                return []
            if existing.status != "open":
                continue
            # Bound the whole episode, avoiding transitive chains across time.
            union = ids.union(existing.event_ids)
            times = [
                Event.model_validate_json(r[0]).occurred_at
                for r in connection.execute("SELECT payload FROM monitoring_events")
                if Event.model_validate_json(r[0]).event_id in union
            ]
            if (
                max(times) - min(times)
            ).total_seconds() > self.clinical_config.fusion_window_seconds:
                continue
            updated = existing.model_copy(update={"event_ids": sorted(union)})
            connection.execute(
                "UPDATE monitoring_alerts SET payload=? WHERE alert_id=?",
                (updated.model_dump_json(), existing.alert_id),
            )
            return []
        # Use a bounded episode rather than emitting every pair.
        compatible.sort(key=lambda e: (e.occurred_at, e.event_id))
        anchor = compatible[0].occurred_at
        compatible = [
            e
            for e in compatible
            if (e.occurred_at - anchor).total_seconds()
            <= self.clinical_config.fusion_window_seconds
        ]
        if event not in compatible:
            compatible = [
                event,
                min(
                    compatible,
                    key=lambda e: abs(
                        (e.occurred_at - event.occurred_at).total_seconds()
                    ),
                ),
            ]
        alert = self._alert(connection, compatible)
        if alert:
            alerts.append(alert)
        return alerts

    def _store_event(self, connection: sqlite3.Connection, event: Event) -> list[Alert]:
        self._session(
            connection,
            event.patient_id,
            event.session_id,
            event.occurred_at,
            event.ended_at,
        )
        row = connection.execute(
            "SELECT payload FROM monitoring_events WHERE event_id = ?",
            (event.event_id,),
        ).fetchone()
        if row:
            if Event.model_validate_json(row[0]) != event:
                raise ValueError("event identifier conflict")
            return self._correlate(connection, event)
        connection.execute(
            "INSERT INTO monitoring_events VALUES (?, ?)",
            (event.event_id, event.model_dump_json()),
        )
        isolated = self._alert(connection, [event])
        return ([isolated] if isolated else []) + self._correlate(connection, event)

    def ingest_event(
        self, event: Event, provenance: dict[str, Any] | None = None
    ) -> list[Alert]:
        return self.ingest_events([(event, provenance)])

    def ingest_events(
        self, items: list[tuple[Event, dict[str, Any] | None]]
    ) -> list[Alert]:
        """Importa eventos atomicamente; conflitos desfazem todo o lote."""
        connection = self._connect()
        try:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                alerts = []
                for event, provenance in items:
                    alerts.extend(self._store_event(connection, event))
                    if provenance is not None:
                        payload = json.dumps(provenance, sort_keys=True)
                        old = connection.execute(
                            "SELECT payload FROM event_provenance WHERE event_id = ?",
                            (event.event_id,),
                        ).fetchone()
                        if old and old[0] != payload:
                            raise ValueError("event provenance conflict")
                        connection.execute(
                            "INSERT OR IGNORE INTO event_provenance VALUES (?, ?)",
                            (event.event_id, payload),
                        )
                return alerts
        finally:
            connection.close()

    def process(self, sample: Measurement) -> ProcessingResult:
        started = perf_counter()
        result = super().process(sample)
        # Repairs correlation after a restart between vitals persistence and fusion.
        connection = self._connect()
        try:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                for row in connection.execute(
                    "SELECT payload FROM monitoring_events"
                ).fetchall():
                    event = Event.model_validate_json(row[0])
                    if (
                        event.session_id == sample.session_id
                        and event.patient_id == sample.patient_id
                    ):
                        result.alerts.extend(self._correlate(connection, event))
        finally:
            connection.close()
        result.processing_ms = (perf_counter() - started) * 1000
        return result

    def ingest_prescription(self, version: PrescriptionVersion) -> dict[str, Any]:
        connection = self._connect()
        try:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                session = self._session(
                    connection,
                    version.patient_id,
                    version.session_id,
                    version.occurred_at,
                    version.occurred_at,
                )
                existing = connection.execute(
                    "SELECT payload FROM prescription_versions "
                    "WHERE session_id = ? AND record_id = ?",
                    (version.session_id, version.record_id),
                ).fetchone()
                if existing:
                    if existing[0] != version.model_dump_json():
                        raise ValueError("prescription identifier conflict")
                    return {"status": "duplicate", "alerts": []}
                rows = connection.execute(
                    "SELECT payload, status FROM prescription_versions "
                    "WHERE session_id = ?",
                    (version.session_id,),
                ).fetchall()
                previous = [
                    PrescriptionVersion.model_validate_json(row[0])
                    for row in rows
                    if row[1] == "accepted"
                ]
                previous = [
                    p for p in previous if p.medication_id == version.medication_id
                ]
                last = max(previous, key=lambda p: p.occurred_at) if previous else None
                status, deviation = "accepted", None
                if last and version.occurred_at <= last.occurred_at:
                    status = "out_of_order"
                elif version.action == "change" and (
                    last is None or last.action == "stop"
                ):
                    status, deviation = (
                        "invalid_transition",
                        "prescription_sequence_issue",
                    )
                elif version.action == "start" and last and last.action != "stop":
                    status, deviation = (
                        "invalid_transition",
                        "prescription_sequence_issue",
                    )
                elif version.action == "stop" and (
                    last is None or last.action == "stop"
                ):
                    status, deviation = (
                        "invalid_transition",
                        "prescription_sequence_issue",
                    )
                elif version.action != "stop" and version.unit != "synthetic_unit":
                    status, deviation = "incompatible_unit", "prescription_unit_issue"
                elif (
                    last and version.action == "change" and not version.expected_change
                ):
                    assert last.dose is not None and version.dose is not None
                    low, high = sorted([last.dose, version.dose])
                    if high > low and (
                        low == 0
                        or high / low >= self.clinical_config.unexpected_dose_ratio
                    ):
                        deviation = "unexpected_prescription_change"
                elif version.action == "stop" and not version.expected_change:
                    deviation = "unexpected_prescription_stop"
                connection.execute(
                    "INSERT INTO prescription_versions VALUES (?, ?, ?, ?)",
                    (
                        version.session_id,
                        version.record_id,
                        version.model_dump_json(),
                        status,
                    ),
                )
                alerts: list[Alert] = []
                if deviation:
                    key = hashlib.sha256(
                        json.dumps(
                            [
                                version.session_id,
                                version.record_id,
                                self.clinical_config.fingerprint,
                            ]
                        ).encode()
                    ).hexdigest()
                    offset = (
                        version.occurred_at
                        - datetime.fromisoformat(session["started_at"])
                    ).total_seconds()
                    event = Event(
                        event_id=f"prescription-{key}",
                        patient_id=version.patient_id,
                        session_id=version.session_id,
                        event_type=deviation,
                        occurred_at=version.occurred_at,
                        ended_at=version.occurred_at,
                        processed_at=datetime.now(UTC),
                        detector_version=self.clinical_config.version,
                        evidence=[
                            Evidence(
                                source_id=version.record_id,
                                modality="prescription",
                                start_seconds=offset,
                                end_seconds=offset,
                                description=(
                                    f"{deviation}; medication={version.medication_id}; "
                                    "previous_record="
                                    f"{last.record_id if last else 'none'}; "
                                    f"previous_dose={last.dose if last else None}; "
                                    f"dose={version.dose}; unit={version.unit}; "
                                    f"expected={version.expected_change}; "
                                    "synthetic rule only"
                                ),
                            )
                        ],
                    )
                    alerts = self._store_event(connection, event)
                return {
                    "status": status,
                    "event_type": deviation,
                    "alerts": [a.model_dump(mode="json") for a in alerts],
                }
        finally:
            connection.close()

    def set_availability(
        self, session_id: str, patient_id: str, modality: str, status: str, reason: str
    ) -> None:
        if (
            modality
            not in {"vitals", "prescription", "audio", "text", "video", "movement"}
            or status not in {"available", "unavailable", "degraded"}
            or not reason.strip()
        ):
            raise ValueError("invalid modality status")
        connection = self._connect()
        try:
            with connection:
                row = connection.execute(
                    "SELECT patient_id FROM monitoring_sessions WHERE session_id = ?",
                    (session_id,),
                ).fetchone()
                if row is None or row[0] != patient_id:
                    raise ValueError("patient does not own session")
                payload = json.dumps(
                    dict(
                        session_id=session_id,
                        patient_id=patient_id,
                        modality=modality,
                        status=status,
                        reason=reason,
                        updated_at=datetime.now(UTC).isoformat(),
                    )
                )
                connection.execute(
                    "INSERT OR REPLACE INTO modality_availability VALUES (?, ?, ?)",
                    (session_id, modality, payload),
                )
        finally:
            connection.close()

    def snapshot(self) -> dict[str, Any]:
        result = super().snapshot()
        connection = self._connect()
        try:
            result["prescriptions"] = [
                {**json.loads(row[0]), "ingestion_status": row[1]}
                for row in connection.execute(
                    "SELECT payload, status FROM prescription_versions ORDER BY rowid"
                )
            ]
            result["prescriptions"].sort(
                key=lambda r: (r["session_id"], r["occurred_at"], r["record_id"])
            )
            result["availability"] = [
                json.loads(row[0])
                for row in connection.execute(
                    "SELECT payload FROM modality_availability "
                    "ORDER BY session_id, modality"
                )
            ]
            result["event_provenance"] = [
                dict(event_id=row[0], **json.loads(row[1]))
                for row in connection.execute(
                    "SELECT event_id, payload FROM event_provenance"
                )
            ]
            result["clinical_config"] = self.clinical_config.model_dump()
            return result
        finally:
            connection.close()
