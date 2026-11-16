"""Experimento pareado de sinais/prescrições nas fixtures funcionais existentes."""

import json
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from monitoramento_clinico.clinical_monitor import ClinicalMonitor
from monitoramento_clinico.contracts import (
    EvaluationCase,
    Event,
    Evidence,
    Manifest,
    Measurement,
    PrescriptionVersion,
    Session,
)
from monitoramento_clinico.data.fixtures import digest
from monitoramento_clinico.data.validation import safe_path
from monitoramento_clinico.event_evaluation import (
    detection_metrics,
    match_events,
    percentile95,
)
from monitoramento_clinico.replay import replay
from monitoramento_clinico.vitals import ProcessingResult, VitalsConfig, VitalsMonitor


def _record_processing(
    timings: list[float], sample: Measurement, result: ProcessingResult
) -> None:
    timings.append(result.processing_ms)


def _references(
    case: EvaluationCase, session: Session, payload: dict[str, Any]
) -> list[Event]:
    from datetime import timedelta

    references = []
    for index, label in enumerate(case.labels):
        source = f"{case.case_id}-reference-{index}"
        if case.modality == "prescription":
            candidates = [
                r
                for r in payload["prescriptions"]
                if PrescriptionVersion.model_validate(r).occurred_at
                == session.started_at + timedelta(seconds=label.start_seconds)
            ]
            ids = {r["record_id"] for r in candidates}
            if len(ids) != 1:
                raise ValueError(
                    "prescription label needs an unambiguous source record"
                )
            source = next(iter(ids))
        references.append(
            Event(
                event_id=f"reference-{case.case_id}-{index}",
                patient_id=case.patient_id,
                session_id=case.session_id,
                event_type=label.event_type,
                occurred_at=session.started_at + timedelta(seconds=label.start_seconds),
                ended_at=session.started_at + timedelta(seconds=label.end_seconds),
                processed_at=session.started_at,
                detector_version="fixture-reference-v1",
                evidence=[
                    Evidence(
                        source_id=source,
                        signal=label.signal,
                        modality=case.modality,
                        start_seconds=label.start_seconds,
                        end_seconds=label.end_seconds,
                        description=f"Reference basis: {label.basis}",
                    )
                ],
            )
        )
    return references


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_type: dict[str, Any] = {}
    scored = [row["comparison"] for row in rows if "comparison" in row]
    for kind in sorted(
        {k for comparison in scored for k in comparison["by_event_type"]}
    ):
        counts_for_type = [
            c["by_event_type"][kind] for c in scored if kind in c["by_event_type"]
        ]
        by_type[kind] = detection_metrics(
            sum(c["true_positive"] for c in counts_for_type),
            sum(c["false_positive"] for c in counts_for_type),
            sum(c["false_negative"] for c in counts_for_type),
        )
    counts = {
        key: sum(
            row["comparison"]["metrics"][key] for row in rows if "comparison" in row
        )
        for key in ("true_positive", "false_positive", "false_negative")
    }
    negative_seconds = sum(
        row["duration_seconds"] for row in rows if row.get("negative_case")
    )
    negative_fp = sum(
        row["comparison"]["metrics"]["false_positive"]
        for row in rows
        if row.get("negative_case")
    )
    return {
        "cases": len(rows),
        "scored_cases": sum("comparison" in row for row in rows),
        "invalid_cases_rejected": sum(
            row["status"] == "rejected_invalid_input" for row in rows
        ),
        "metrics": detection_metrics(
            counts["true_positive"], counts["false_positive"], counts["false_negative"]
        ),
        "by_event_type": by_type,
        "negative_duration_seconds": negative_seconds,
        "false_positives_on_negative_cases": negative_fp,
        "false_alerts_per_negative_hour": negative_fp * 3600 / negative_seconds
        if negative_seconds
        else None,
        "processing_p95_ms": percentile95(
            [v for row in rows for v in row.get("processing_ms", [])]
        ),
        "confirmation_to_alert_p95_seconds": percentile95(
            [v for row in rows for v in row.get("confirmation_to_alert_seconds", [])]
        ),
        "onset_to_alert_p95_seconds": percentile95(
            [v for row in rows for v in row.get("onset_to_alert_seconds", [])]
        ),
    }


def evaluate_local_fixtures(
    fixtures: Path,
    config: VitalsConfig,
    protocol: dict[str, Any],
    split: str = "development",
    speed: float = 0,
    case_id: str | None = None,
) -> dict[str, Any]:
    if split not in {"development", "validation", "test"} or speed not in {0, 1}:
        raise ValueError("select a valid split and speed 0 or 1")
    matching = protocol["event_matching"]
    expected = {
        "strategy": "one_to_one_nearest_onset",
        "tie_breaker": "event_id_lexicographic",
        "text_and_prescription": "source_record_or_mention_id",
    }
    if any(matching.get(k) != v for k, v in expected.items()):
        raise ValueError("unsupported matching protocol")
    manifest = Manifest.model_validate_json((fixtures / "manifest.json").read_text())
    cases = [
        case
        for case in manifest.cases
        if case.split == split
        and case.modality in {"vitals", "prescription"}
        and (case_id is None or case.case_id == case_id)
    ]
    if not cases:
        raise ValueError("no supported cases for selection")
    sessions = {s.session_id: s for s in manifest.sessions}
    rows: list[dict[str, Any]] = []
    with TemporaryDirectory(prefix="phase4-evaluation-") as temporary:
        for case in cases:
            path = safe_path(fixtures, case.path)
            if digest(path) != case.sha256:
                raise ValueError("case checksum mismatch")
            payload = json.loads(path.read_text())
            session = sessions[case.session_id]
            if (payload["patient_id"], payload["session_id"]) != (
                case.patient_id,
                case.session_id,
            ) or session.patient_id != case.patient_id:
                raise ValueError("case identity mismatch")
            variants = (
                ["instant", "temporal"]
                if case.modality == "vitals"
                else ["prescription_rules"]
            )
            for variant in variants:
                row: dict[str, Any] = {
                    "case_id": case.case_id,
                    "scenario_id": case.scenario_id,
                    "modality": case.modality,
                    "variant": variant,
                    "input_sha256": case.sha256,
                    "status": "completed",
                }
                try:
                    records = (
                        [Measurement.model_validate(r) for r in payload["measurements"]]
                        if case.modality == "vitals"
                        else [
                            PrescriptionVersion.model_validate(r)
                            for r in payload["prescriptions"]
                        ]
                    )
                except ValueError as error:
                    if case.input_status != "invalid":
                        raise
                    row.update(
                        status="rejected_invalid_input", error_type=type(error).__name__
                    )
                    rows.append(row)
                    continue
                if case.input_status != "valid":
                    raise ValueError("fixture input status differs from parsed records")
                if any(
                    (r.patient_id, r.session_id) != (case.patient_id, case.session_id)
                    for r in records
                ):
                    raise ValueError("record identity mismatch")
                database = Path(temporary) / f"{case.case_id}-{variant}.db"
                timings: list[float] = []
                if case.modality == "vitals":
                    selected = (
                        VitalsConfig.model_validate(
                            {
                                **config.model_dump(),
                                "version": "baseline-instant-v1",
                                "persistence_seconds": 0,
                            }
                        )
                        if variant == "instant"
                        else config
                    )
                    monitor: VitalsMonitor = VitalsMonitor(database, selected)
                    measurements = [
                        Measurement.model_validate(r) for r in payload["measurements"]
                    ]
                    playback = replay(
                        monitor,
                        session,
                        measurements,
                        speed=speed,
                        on_sample=partial(_record_processing, timings),
                        source_id=case.case_id,
                    )
                    row.update(
                        detector_config=selected.model_dump(),
                        confirmation_to_alert_seconds=playback[
                            "confirmation_to_alert_seconds"
                        ],
                        onset_to_alert_seconds=playback["onset_to_alert_seconds"],
                        processing_ms=timings,
                        ingestion_statuses=playback["statuses"],
                    )
                    monitored_types = {"persistent_deviation", "trend_deviation"}
                else:
                    from time import perf_counter

                    clinical = ClinicalMonitor(database, config)
                    clinical.register_session(session)
                    statuses: dict[str, int] = {}
                    for record in payload["prescriptions"]:
                        started = perf_counter()
                        response = clinical.ingest_prescription(
                            PrescriptionVersion.model_validate(record)
                        )
                        timings.append((perf_counter() - started) * 1000)
                        status = response["status"]
                        statuses[status] = statuses.get(status, 0) + 1
                    monitor = clinical
                    row.update(
                        processing_ms=timings,
                        ingestion_statuses=statuses,
                        detector_config=clinical.clinical_config.model_dump(),
                    )
                    monitored_types = {
                        "unexpected_prescription_change",
                        "unexpected_prescription_stop",
                        "prescription_unit_issue",
                        "prescription_sequence_issue",
                    }
                snapshot = monitor.snapshot()
                all_events = [Event.model_validate(e) for e in snapshot["events"]]
                predictions = [e for e in all_events if e.event_type in monitored_types]
                references = _references(case, session, payload)
                if any(e.event_type not in monitored_types for e in references):
                    raise ValueError("reference type not covered by evaluation scope")
                times = [r.occurred_at for r in records]
                row.update(
                    comparison=match_events(
                        predictions, references, matching["onset_tolerance_seconds"]
                    ),
                    duration_seconds=(max(times) - min(times)).total_seconds(),
                    negative_case=not references,
                    predictions=[e.model_dump(mode="json") for e in predictions],
                    references=[e.model_dump(mode="json") for e in references],
                    unscored_events=[
                        e.model_dump(mode="json")
                        for e in all_events
                        if e.event_type not in monitored_types
                    ],
                )
                rows.append(row)
    return {
        "scope": "synthetic functional fixtures; not independent clinical validation",
        "split": split,
        "case_selection": case_id,
        "speed": speed,
        "latency_scope": "cadence_1x_synthetic_playback"
        if speed == 1
        else "processing_only_accelerated",
        "clinical_validation": False,
        "representative_media_evaluated": False,
        "manifest_sha256": digest(fixtures / "manifest.json"),
        "protocol": protocol,
        "label_limitations": [
            "Signal-specific synthetic references v2; "
            "trend and limit deviations are scored separately",
            "Prescription references cover dose changes, stop and unit issues; "
            "sequence errors require additional annotated cases",
            "Negative duration is last minus first observed timestamp, "
            "not the full session; short recordings do not establish long-term rates",
        ],
        "summaries": {
            variant: _summarize([r for r in rows if r["variant"] == variant])
            for variant in sorted({r["variant"] for r in rows})
        },
        "cases": rows,
    }
