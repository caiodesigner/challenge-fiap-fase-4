"""Auditoria local; chamadores devem sanitizar o conteúdo antes de registrar."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any, Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def mask_identifier(value: str) -> str:
    """Produz referência estável por hash, sem garantia de anonimização."""

    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"sha256:{digest}"


class AuditMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detector_version: str = "not_configured"
    pipeline_version: str = "phase4-base-v1"
    modality: str = "not_configured"


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    execution_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    event_type: str
    actor_role: str
    status: str
    session_ref: str
    patient_ref: str | None = None
    duration_ms: float | None = Field(default=None, ge=0)
    metadata: AuditMetadata
    details: dict[str, Any] = Field(default_factory=dict)


class AuditRecorder(Protocol):
    def record(self, event: AuditEvent) -> None: ...

    def events_for(self, execution_id: str) -> list[AuditEvent]: ...


class InMemoryAuditRecorder:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def record(self, event: AuditEvent) -> None:
        self.events.append(event)

    def events_for(self, execution_id: str) -> list[AuditEvent]:
        return [event for event in self.events if event.execution_id == execution_id]


class JsonlAuditRecorder:
    """Append-only local para o protótipo; um evento JSON por linha."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def record(self, event: AuditEvent) -> None:
        serialized = event.model_dump_json() + "\n"
        with self._lock, self.path.open("a", encoding="utf-8") as stream:
            stream.write(serialized)
            stream.flush()

    def events_for(self, execution_id: str) -> list[AuditEvent]:
        if not self.path.exists():
            return []
        events: list[AuditEvent] = []
        with self.path.open(encoding="utf-8") as stream:
            for line in stream:
                payload = json.loads(line)
                if payload.get("execution_id") == execution_id:
                    events.append(AuditEvent.model_validate(payload))
        return events
