from datetime import timedelta

import pytest
from test_clinical_monitor import START, event, monitor, session

from monitoramento_clinico.media_alignment import align_media_report


def report() -> dict:
    origin = START + timedelta(days=20)
    original = event("source", "text", 5).model_copy(
        update={
            "occurred_at": origin + timedelta(seconds=5),
            "ended_at": origin + timedelta(seconds=5),
        }
    )
    return {
        "patient_id": "PAT-SYN-001",
        "session_id": "s1",
        "started_at": origin.isoformat(),
        "status": "completed",
        "events": [original.model_dump(mode="json")],
        "timeline_origin": "processing_start_assigned_not_capture_time",
    }


def test_explicit_alignment_preserves_origin_and_is_idempotent(tmp_path) -> None:
    source = report()
    aligned = align_media_report(
        source, session(), START + timedelta(seconds=10), "synthetic"
    )
    e, provenance = aligned[0]
    assert e.occurred_at == START + timedelta(seconds=15)
    assert e.evidence[0].start_seconds == 15
    assert provenance["original_event_id"] == "source"
    m = monitor(tmp_path)
    m.ingest_events(aligned)
    assert m.ingest_events(aligned) == []
    assert m.snapshot()["event_provenance"][0]["association"] == "synthetic"
    assert source["events"][0]["event_id"] == "source"


def test_identity_clock_and_interval_must_be_explicit() -> None:
    for change, message in [
        ({"patient_id": "PAT-SYN-002"}, "patient"),
        ({"timeline_origin": "unknown"}, "timeline"),
        ({"status": "failed"}, "usable"),
    ]:
        with pytest.raises(ValueError, match=message):
            align_media_report({**report(), **change}, session(), START, "synthetic")
    with pytest.raises(ValueError, match="outside"):
        align_media_report(
            report(), session(), START + timedelta(minutes=5), "synthetic"
        )
    with pytest.raises(ValueError, match="timezone"):
        align_media_report(report(), session(), START.replace(tzinfo=None), "synthetic")


def test_batch_rolls_back_on_conflicting_provenance(tmp_path) -> None:
    m = monitor(tmp_path)
    m.ingest_event(event("old", "text", 5), {"origin": "original"})
    before = m.snapshot()
    with pytest.raises(ValueError, match="provenance conflict"):
        m.ingest_events(
            [
                (event("new", "video", 5), None),
                (event("old", "text", 5), {"origin": "changed"}),
            ]
        )
    assert m.snapshot() == before
