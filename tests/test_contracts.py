from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from monitoramento_clinico.contracts import (
    Measurement,
    Patient,
    ReferenceLabel,
    Session,
)


def test_utc_conversion_and_naive_timestamp_rejection() -> None:
    payload = {
        "session_id": "s",
        "patient_id": "PAT-SYN-001",
        "started_at": "2026-01-01T03:00:00-03:00",
        "ended_at": "2026-01-01T03:01:00-03:00",
    }
    session = Session.model_validate(payload)
    assert session.started_at == datetime(2026, 1, 1, 6, tzinfo=UTC)
    with pytest.raises(ValidationError):
        Session.model_validate({**payload, "started_at": "2026-01-01T03:00:00"})
    with pytest.raises(ValidationError):
        Session.model_validate({**payload, "ended_at": "2025-01-01T00:00:00Z"})


def test_measurement_rejects_incompatible_unit_and_nonfinite_value() -> None:
    payload = {
        "record_id": "r",
        "patient_id": "p",
        "session_id": "s",
        "occurred_at": "2026-01-01T00:00:00Z",
        "ingested_at": "2026-01-01T00:00:00Z",
        "signal": "heart_rate",
        "value": 70,
        "unit": "bpm",
    }
    assert Measurement.model_validate(payload).value == 70
    for patch in ({"unit": "%"}, {"value": float("nan")}, {"value": float("inf")}):
        with pytest.raises(ValidationError):
            Measurement.model_validate({**payload, **patch})


def test_patient_scope_and_label_interval() -> None:
    with pytest.raises(ValidationError):
        Patient(patient_id="PAT-SYN-001", age_years=12)
    with pytest.raises(ValidationError):
        ReferenceLabel(
            event_type="change", start_seconds=10, end_seconds=5, basis="synthetic_rule"
        )
