from pathlib import Path

import pytest
from pydantic import ValidationError

from monitoramento_clinico.audit.recorder import (
    AuditEvent,
    AuditMetadata,
    InMemoryAuditRecorder,
    JsonlAuditRecorder,
    mask_identifier,
)


def event(execution_id: str) -> AuditEvent:
    return AuditEvent(
        execution_id=execution_id,
        event_type="measurement_received",
        actor_role="pipeline",
        status="received",
        session_ref=mask_identifier("session-1"),
        patient_ref=mask_identifier("PAT-SYN-001"),
        metadata=AuditMetadata(detector_version="rules-v1", modality="vitals"),
        details={"sample_count": 1},
    )


def test_audit_survives_restart_and_filters_executions(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    recorder = JsonlAuditRecorder(path)
    recorder.record(event("run-1"))
    recorder.record(event("run-2"))
    restored = JsonlAuditRecorder(path).events_for("run-1")
    assert len(restored) == 1
    assert restored[0].metadata.modality == "vitals"
    offset = restored[0].timestamp.utcoffset()
    assert offset is not None and offset.total_seconds() == 0
    assert len(path.read_text().splitlines()) == 2
    assert "PAT-SYN-001" not in path.read_text()
    assert "session-1" not in path.read_text()


def test_memory_recorder_isolates_executions() -> None:
    recorder = InMemoryAuditRecorder()
    recorder.record(event("run-1"))
    assert len(recorder.events_for("run-1")) == 1
    assert recorder.events_for("run-2") == []


def test_missing_audit_file_has_no_events(tmp_path: Path) -> None:
    assert JsonlAuditRecorder(tmp_path / "missing.jsonl").events_for("x") == []


def test_audit_rejects_negative_duration_and_unknown_fields() -> None:
    payload = event("run-1").model_dump()
    with pytest.raises(ValidationError):
        AuditEvent.model_validate({**payload, "duration_ms": -1})
    with pytest.raises(ValidationError):
        AuditEvent.model_validate({**payload, "unknown": "value"})


def test_hash_is_stable_and_different_between_identifiers() -> None:
    assert mask_identifier("one") == mask_identifier("one")
    assert mask_identifier("one") != mask_identifier("two")
