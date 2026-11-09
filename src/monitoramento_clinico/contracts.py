"""Contratos iniciais de ingestão, evidências e avaliação da fase 4."""

from datetime import UTC, datetime
from typing import Annotated, Literal, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)


def utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp requires timezone")
    return value.astimezone(UTC)


Timestamp = Annotated[datetime, AfterValidator(utc)]
Identifier = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
Modality = Literal["vitals", "prescription", "video", "movement", "audio", "text"]
Split = Literal["development", "validation", "test"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Patient(Contract):
    patient_id: Annotated[str, StringConstraints(pattern=r"^PAT-SYN-\d{3}$")]
    age_years: int = Field(ge=18, le=120)
    synthetic: Literal[True] = True


class Session(Contract):
    session_id: Identifier
    patient_id: Identifier
    started_at: Timestamp
    ended_at: Timestamp

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.ended_at < self.started_at:
            raise ValueError("session end precedes start")
        return self


class Measurement(Contract):
    record_id: Identifier
    patient_id: Identifier
    session_id: Identifier
    occurred_at: Timestamp
    ingested_at: Timestamp
    signal: Literal["heart_rate", "systolic", "diastolic", "spo2"]
    value: float
    unit: Literal["bpm", "mmHg", "%"]
    quality: Literal["valid", "artifact", "missing"] = "valid"

    @model_validator(mode="after")
    def compatible_unit(self) -> Self:
        expected = {
            "heart_rate": "bpm",
            "systolic": "mmHg",
            "diastolic": "mmHg",
            "spo2": "%",
        }
        if self.unit != expected[self.signal]:
            raise ValueError("unit incompatible with signal")
        return self


class PrescriptionVersion(Contract):
    record_id: Identifier
    patient_id: Identifier
    session_id: Identifier
    medication_id: Identifier
    occurred_at: Timestamp
    action: Literal["start", "change", "stop"]
    dose: float | None = Field(default=None, ge=0)
    unit: Literal["synthetic_unit", "incompatible_unit"] | None = None
    expected_change: bool = False
    reason: str | None = None

    @model_validator(mode="after")
    def complete(self) -> Self:
        if self.action != "stop" and (self.dose is None or self.unit is None):
            raise ValueError("active prescription requires dose and unit")
        if self.expected_change and not self.reason:
            raise ValueError("expected change requires reason")
        return self


class MediaAsset(Contract):
    asset_id: Identifier
    patient_id: Identifier
    session_id: Identifier
    modality: Literal["audio", "video"]
    path: Identifier
    sha256: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
    duration_seconds: float = Field(gt=0)
    content_kind: Literal["technical_synthetic", "staged", "external"]
    source_group: Identifier
    consent_or_license: Identifier
    cloud_upload_allowed: bool = False


class Evidence(Contract):
    source_id: Identifier
    modality: Modality
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(ge=0)
    description: Identifier

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.end_seconds < self.start_seconds:
            raise ValueError("evidence end precedes start")
        return self


class Event(Contract):
    event_id: Identifier
    patient_id: Identifier
    session_id: Identifier
    event_type: Identifier
    occurred_at: Timestamp
    ended_at: Timestamp
    processed_at: Timestamp
    detector_version: Identifier
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.ended_at < self.occurred_at:
            raise ValueError("event end precedes start")
        return self


class Alert(Contract):
    alert_id: Identifier
    deduplication_key: Identifier
    patient_id: Identifier
    session_id: Identifier
    event_ids: list[Identifier] = Field(min_length=1)
    emitted_at: Timestamp
    severity: Literal["observation", "attention", "priority"]
    status: Literal["open", "acknowledged", "closed"] = "open"
    review: Literal["confirmed", "false_positive", "inconclusive"] | None = None


class ReferenceLabel(Contract):
    event_type: Identifier
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(ge=0)
    basis: Literal["synthetic_rule", "manual_annotation"]

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.end_seconds < self.start_seconds:
            raise ValueError("label end precedes start")
        return self


class EvaluationCase(Contract):
    case_id: Identifier
    scenario_id: Identifier
    patient_id: Identifier
    session_id: Identifier
    source_group: Identifier
    split: Split
    modality: Modality
    path: Identifier
    sha256: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
    input_status: Literal["valid", "invalid", "insufficient"]
    expected_outcome: Identifier
    labels: list[ReferenceLabel]


class Manifest(Contract):
    schema_version: Literal["1.0"] = "1.0"
    purpose: Literal["functional_fixtures_not_clinical_validation"]
    seed: int
    source: Identifier
    consent_or_license: Identifier
    patients: list[Patient]
    sessions: list[Session]
    assets: list[MediaAsset]
    cases: list[EvaluationCase]
