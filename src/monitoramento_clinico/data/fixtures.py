"""Fixtures determinísticas; não representam pacientes nem validação clínica."""

import hashlib
import json
import math
import random
import struct
import wave
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from monitoramento_clinico.contracts import Manifest

SEED = 42
SCENARIOS = {
    "vitals": ["VIT-01", "VIT-02", "VIT-03", "VIT-04", "VIT-05"],
    "prescription": ["PRE-01", "PRE-02", "PRE-03", "PRE-04", "PRE-05"],
    "video": ["VID-01", "VID-02", "VID-03", "VID-04", "VID-05"],
    "movement": ["MOV-01", "MOV-02", "MOV-03", "MOV-04", "MOV-05"],
    "audio": ["AUD-01", "AUD-02", "AUD-05", "AUD-05", "AUD-05"],
    "text": ["AUD-01", "AUD-03", "AUD-04", "AUD-06", "AUD-05"],
}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate_dataset(destination: Path) -> Manifest:
    """Recria somente o diretório dedicado de fixtures, sem rede ou dados reais."""
    rng = random.Random(SEED)
    patients: list[dict[str, Any]] = []
    sessions: list[dict[str, Any]] = []
    cases: list[dict[str, Any]] = []
    assets: list[dict[str, Any]] = []
    for index, split in enumerate(("development", "validation", "test"), 1):
        patient = f"PAT-SYN-{index:03d}"
        session = f"SESSION-{index:03d}"
        group = f"SYNTHETIC-SOURCE-{index:03d}"
        start = datetime(2026, 1, index, tzinfo=UTC)
        patients.append({"patient_id": patient, "age_years": 30 + index})
        sessions.append(
            {
                "session_id": session,
                "patient_id": patient,
                "started_at": start.isoformat(),
                "ended_at": (start + timedelta(seconds=60)).isoformat(),
            }
        )
        wav_path = destination / split / "technical-tone.wav"
        wav_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(wav_path), "wb") as stream:
            stream.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
            stream.writeframes(
                b"".join(
                    struct.pack(
                        "<h",
                        int(
                            2000
                            * math.sin(2 * math.pi * (200 + index * 30) * t / 16000)
                        ),
                    )
                    for t in range(16000)
                )
            )
        assets.append(
            {
                "asset_id": f"TONE-{index}",
                "patient_id": patient,
                "session_id": session,
                "modality": "audio",
                "path": wav_path.relative_to(destination).as_posix(),
                "sha256": digest(wav_path),
                "duration_seconds": 1,
                "content_kind": "technical_synthetic",
                "source_group": group,
                "consent_or_license": "author-generated technical fixture",
                "cloud_upload_allowed": False,
            }
        )
        for modality, scenarios in SCENARIOS.items():
            for variant, scenario in enumerate(scenarios):
                case_id = f"{split}-{modality}-{variant + 1}"
                status = "valid"
                outcome = "no_event"
                labels: list[dict[str, Any]] = []
                payload: dict[str, Any] = {
                    "patient_id": patient,
                    "session_id": session,
                    "representation": "synthetic_fixture",
                }
                if modality == "vitals":
                    rows = []
                    for second in range(20):
                        for signal, unit, normal in [
                            ("heart_rate", "bpm", 75),
                            ("systolic", "mmHg", 120),
                            ("diastolic", "mmHg", 80),
                            ("spo2", "%", 98),
                        ]:
                            value = normal + round(rng.uniform(-0.2, 0.2), 2)
                            if variant == 1 and second >= 10:
                                value += -12 if signal == "spo2" else 50
                            if variant == 2 and second >= 10:
                                value += (second - 9) * (
                                    -0.7 if signal == "spo2" else 3
                                )
                            if variant == 3 and second == 10:
                                value += -15 if signal == "spo2" else 70
                            when = (start + timedelta(seconds=second)).isoformat()
                            rows.append(
                                {
                                    "record_id": f"{case_id}-{signal}-{second}",
                                    "patient_id": patient,
                                    "session_id": session,
                                    "occurred_at": when,
                                    "ingested_at": when,
                                    "signal": signal,
                                    "unit": unit,
                                    "value": value,
                                    "quality": "artifact"
                                    if variant == 3 and second == 10
                                    else "valid",
                                }
                            )
                    if variant == 4:
                        rows[0]["unit"] = "%"
                        status, outcome = "invalid", "reject_unit"
                    payload["measurements"] = rows
                elif modality == "prescription":
                    rows = []
                    for version in range(2):
                        rows.append(
                            {
                                "record_id": f"{case_id}-version-{version}",
                                "patient_id": patient,
                                "session_id": session,
                                "medication_id": "SYNTHETIC-MED-A",
                                "occurred_at": (
                                    start + timedelta(seconds=version * 10)
                                ).isoformat(),
                                "action": "start" if version == 0 else "change",
                                "dose": 1 if version == 0 or variant == 0 else 4,
                                "unit": "synthetic_unit",
                                "expected_change": False,
                            }
                        )
                    if variant == 1:
                        rows[1].update(expected_change=True, reason="planned fixture")
                    if variant == 3:
                        rows[1]["unit"] = "incompatible_unit"
                        outcome = "inconsistent_units"
                    if variant == 4:
                        rows[1].update(action="stop", dose=None, unit=None)
                        rows.append(dict(rows[1]))
                        rows.append(
                            {
                                **rows[0],
                                "record_id": f"{case_id}-restart",
                                "occurred_at": (
                                    start + timedelta(seconds=15)
                                ).isoformat(),
                            }
                        )
                        outcome = "deduplicate_and_preserve_history"
                    payload["prescriptions"] = rows
                elif modality == "text":
                    texts = [
                        "Estou confortável.",
                        "Estou com falta de ar.",
                        "Não estou com falta de ar.",
                        "Ontem tive falta de ar, agora estou bem.",
                        "",
                    ]
                    payload["transcript"] = texts[variant]
                    payload["origin"] = "scripted_text_not_azure_transcription"
                    outcome = [
                        "no_event",
                        "critical_mention",
                        "negated_mention",
                        "historical_mention",
                        "insufficient_text",
                    ][variant]
                    if variant == 4:
                        status = "insufficient"
                else:
                    frames = []
                    for second in range(20):
                        value = round(0.5 + 0.4 * math.sin(second / 3), 3)
                        frames.append(
                            {
                                "second": second,
                                "left": value,
                                "right": value / 3
                                if variant == 1 and second >= 10
                                else value,
                                "visible": variant != 3,
                            }
                        )
                    payload["samples"] = frames
                    payload["representation"] = (
                        "synthetic_energy_envelope_not_voice"
                        if modality == "audio"
                        else "synthetic_features_not_video"
                    )
                    if variant == 2 or (modality == "audio" and variant == 1):
                        for frame in frames[10:]:
                            frame.update(
                                left=1 if modality == "movement" else 0,
                                right=1 if modality == "movement" else 0,
                            )
                    if variant == 3:
                        status, outcome = "insufficient", "quality_issue"
                    if modality == "audio" and variant == 2:
                        for frame in frames:
                            frame.update(left=0, right=0)
                        status, outcome = "insufficient", "silence"
                    if variant == 4:
                        if modality == "movement":
                            for frame in frames[10:]:
                                frame["second"] += 20
                            outcome = "temporal_gap"
                        else:
                            payload["samples"] = "corrupt fixture"
                            status, outcome = "invalid", "reject_format"
                positive_types = {
                    "vitals": {1: "persistent_deviation", 2: "trend_deviation"},
                    "prescription": {2: "unexpected_prescription_change"},
                    "video": {1: "asymmetry", 2: "interruption"},
                    "movement": {1: "activity_change", 2: "attempt_to_rise"},
                    "audio": {1: "pause_change"},
                    "text": {1: "critical_mention"},
                }
                if variant in positive_types[modality]:
                    outcome = positive_types[modality][variant]
                    labels = [
                        {
                            "event_type": outcome,
                            "start_seconds": 0 if modality == "text" else 10,
                            "end_seconds": 0
                            if modality == "text"
                            else (10 if modality == "prescription" else 19),
                            "basis": "synthetic_rule",
                        }
                    ]
                relative = Path(split) / f"{case_id}.json"
                path = destination / relative
                write_json(path, payload)
                cases.append(
                    {
                        "case_id": case_id,
                        "scenario_id": scenario,
                        "patient_id": patient,
                        "session_id": session,
                        "source_group": group,
                        "split": split,
                        "modality": modality,
                        "path": relative.as_posix(),
                        "sha256": digest(path),
                        "input_status": status,
                        "expected_outcome": outcome,
                        "labels": labels,
                    }
                )
    manifest = Manifest.model_validate(
        {
            "purpose": "functional_fixtures_not_clinical_validation",
            "seed": SEED,
            "source": "deterministic project generator; no real patient data",
            "consent_or_license": "author-generated; LicenseRef-Proprietary",
            "patients": patients,
            "sessions": sessions,
            "assets": assets,
            "cases": cases,
        }
    )
    write_json(destination / "manifest.json", manifest.model_dump(mode="json"))
    for split in ("development", "validation", "test"):
        write_json(
            destination / "splits" / f"{split}.json",
            [case.case_id for case in manifest.cases if case.split == split],
        )
    return manifest
