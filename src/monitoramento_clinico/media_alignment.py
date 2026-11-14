"""Alinhamento explícito de mídia, separando processamento e captura."""

import hashlib
import json
from datetime import datetime
from typing import Any, Literal

from monitoramento_clinico.contracts import Event, Evidence, Session, utc


def align_media_report(
    report: dict[str, Any],
    session: Session,
    capture_started_at: datetime,
    association: Literal["synthetic", "capture_time_informed"],
) -> list[tuple[Event, dict[str, Any] | None]]:
    capture_started_at = utc(capture_started_at)
    if association not in {"synthetic", "capture_time_informed"}:
        raise ValueError("explicit timeline association required")
    if report.get("patient_id") != session.patient_id:
        raise ValueError("media patient does not own session")
    if report.get("status") not in {"completed", "partial"}:
        raise ValueError("report is not usable")
    if report.get("timeline_origin") != "processing_start_assigned_not_capture_time":
        raise ValueError("unsupported media timeline")
    origin = utc(datetime.fromisoformat(report["started_at"]))
    report_hash = hashlib.sha256(
        json.dumps(report, sort_keys=True).encode()
    ).hexdigest()
    aligned: list[tuple[Event, dict[str, Any] | None]] = []
    for payload in report["events"]:
        original = Event.model_validate(payload)
        if (original.patient_id, original.session_id) != (
            report["patient_id"],
            report["session_id"],
        ):
            raise ValueError("event differs from report identity")
        if not {e.modality for e in original.evidence} <= {
            "audio",
            "text",
            "video",
            "movement",
        }:
            raise ValueError("unsupported media modality")
        begin = capture_started_at + (original.occurred_at - origin)
        end = capture_started_at + (original.ended_at - origin)
        if not session.started_at <= begin <= end <= session.ended_at:
            raise ValueError("aligned event outside session")
        offset = (capture_started_at - session.started_at).total_seconds()
        evidence = [
            Evidence.model_validate(
                {
                    **e.model_dump(),
                    "start_seconds": e.start_seconds + offset,
                    "end_seconds": e.end_seconds + offset,
                }
            )
            for e in original.evidence
        ]
        key = hashlib.sha256(
            json.dumps(
                [
                    report_hash,
                    original.event_id,
                    session.session_id,
                    capture_started_at.isoformat(),
                    association,
                ]
            ).encode()
        ).hexdigest()
        event = Event.model_validate(
            {
                **original.model_dump(),
                "event_id": f"aligned-{key}",
                "session_id": session.session_id,
                "occurred_at": begin,
                "ended_at": end,
                "evidence": evidence,
            }
        )
        aligned.append(
            (
                event,
                {
                    "original_event_id": original.event_id,
                    "original_session_id": original.session_id,
                    "original_event": original.model_dump(mode="json"),
                    "report_sha256": report_hash,
                    "capture_started_at": capture_started_at.isoformat(),
                    "association": association,
                    "text_timing": "utterance start only; no word alignment"
                    if any(e.modality == "text" for e in evidence)
                    else None,
                },
            )
        )
    return aligned
