"""Validação de integridade, vínculos e isolamento das fixtures multimodais."""

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from monitoramento_clinico.contracts import Manifest, Measurement, PrescriptionVersion
from monitoramento_clinico.data.anonymization import forbidden_keys, scan_text
from monitoramento_clinico.data.fixtures import digest


def safe_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if Path(relative).is_absolute() or not path.is_relative_to(root.resolve()):
        raise ValueError("dataset path escapes root")
    return path


def check_identifiers(value: Any) -> None:
    if isinstance(value, dict):
        if forbidden_keys(value):
            raise ValueError("forbidden identifier field")
        for key, child in value.items():
            # Hashes tipados podem conter sequências que parecem telefones.
            if (
                key == "sha256"
                and isinstance(child, str)
                and re.fullmatch(r"[0-9a-f]{64}", child)
            ):
                continue
            check_identifiers(child)
    elif isinstance(value, list):
        for child in value:
            check_identifiers(child)
    elif isinstance(value, str) and scan_text(value):
        raise ValueError("possible textual identifier")


def validate_payload(modality: str, payload: dict[str, Any]) -> None:
    if modality in {"vitals", "prescription"}:
        key = "measurements" if modality == "vitals" else "prescriptions"
        if not isinstance(payload.get(key), list) or not payload[key]:
            raise ValueError("missing records")
        for row in payload[key]:
            record = (
                Measurement.model_validate(row)
                if modality == "vitals"
                else PrescriptionVersion.model_validate(row)
            )
            if (record.patient_id, record.session_id) != (
                payload["patient_id"],
                payload["session_id"],
            ):
                raise ValueError("record identity mismatch")
    elif modality == "text":
        if not isinstance(payload.get("transcript"), str):
            raise ValueError("missing transcript")
    else:
        samples = payload.get("samples")
        if not isinstance(samples, list) or not samples:
            raise ValueError("invalid samples")
        for frame in samples:
            if not isinstance(frame, dict) or not isinstance(
                frame.get("visible"), bool
            ):
                raise ValueError("invalid sample shape")
            for field in ("second", "left", "right"):
                value = frame.get(field)
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError("sample values must be numeric")
                if not math.isfinite(value) or value < 0:
                    raise ValueError("sample values must be finite and nonnegative")


def validate_dataset(root: Path) -> dict[str, Any]:
    manifest = Manifest.model_validate_json((root / "manifest.json").read_text())
    check_identifiers(manifest.model_dump(mode="json"))
    patients = {p.patient_id for p in manifest.patients}
    sessions = {s.session_id: s for s in manifest.sessions}
    if len(patients) != len(manifest.patients) or len(sessions) != len(
        manifest.sessions
    ):
        raise ValueError("duplicate patient or session")
    for known_session in sessions.values():
        if known_session.patient_id not in patients:
            raise ValueError("unknown session patient")
    case_ids: set[str] = set()
    partitions: dict[tuple[str, str], str] = {}
    counts: Counter[str] = Counter()
    file_hashes: dict[str, str] = {}
    for case in manifest.cases:
        if case.case_id in case_ids:
            raise ValueError("duplicate case")
        case_ids.add(case.case_id)
        session = sessions.get(case.session_id)
        if session is None or session.patient_id != case.patient_id:
            raise ValueError("case identity mismatch")
        for kind, value in (
            ("patient", case.patient_id),
            ("session", case.session_id),
            ("source", case.source_group),
        ):
            previous = partitions.setdefault((kind, value), case.split)
            if previous != case.split:
                raise ValueError(f"split leakage: {kind}")
        previous_split = file_hashes.setdefault(case.sha256, case.split)
        if previous_split != case.split:
            raise ValueError("duplicate content across splits")
        path = safe_path(root, case.path)
        if digest(path) != case.sha256:
            raise ValueError(f"checksum mismatch: {case.case_id}")
        payload = json.loads(path.read_text())
        check_identifiers(payload)
        if (payload.get("patient_id"), payload.get("session_id")) != (
            case.patient_id,
            case.session_id,
        ):
            raise ValueError("payload identity mismatch")
        try:
            validate_payload(case.modality, payload)
        except (ValidationError, ValueError, TypeError, KeyError):
            if case.input_status != "invalid":
                raise ValueError(
                    f"unexpected invalid payload: {case.case_id}"
                ) from None
        else:
            if case.input_status == "invalid":
                raise ValueError(f"invalid fixture was accepted: {case.case_id}")
        duration = (session.ended_at - session.started_at).total_seconds()
        if any(label.end_seconds > duration for label in case.labels):
            raise ValueError("label outside session")
        counts[f"{case.split}/{case.modality}"] += 1
    for split in ("development", "validation", "test"):
        members = json.loads((root / "splits" / f"{split}.json").read_text())
        expected = {c.case_id for c in manifest.cases if c.split == split}
        if len(members) != len(set(members)) or set(members) != expected:
            raise ValueError("split index mismatch")
    asset_ids: set[str] = set()
    for asset in manifest.assets:
        if asset.asset_id in asset_ids:
            raise ValueError("duplicate asset")
        asset_ids.add(asset.asset_id)
        session = sessions.get(asset.session_id)
        if session is None or session.patient_id != asset.patient_id:
            raise ValueError("asset identity mismatch")
        patient_split = partitions.get(("patient", asset.patient_id))
        source_split = partitions.get(("source", asset.source_group))
        if patient_split is None or source_split != patient_split:
            raise ValueError("asset source leakage")
        if digest(safe_path(root, asset.path)) != asset.sha256:
            raise ValueError("asset checksum mismatch")
        prior = file_hashes.setdefault(asset.sha256, patient_split)
        if prior != patient_split:
            raise ValueError("asset duplicate across splits")
    return {
        "cases": len(case_ids),
        "patients": len(patients),
        "assets": len(manifest.assets),
        "distribution": dict(sorted(counts.items())),
        "scope": manifest.purpose,
    }
