"""Demonstração sintética de desenvolvimento, sem modelos ou serviços externos."""

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from monitoramento_clinico.clinical_monitor import ClinicalMonitor
from monitoramento_clinico.contracts import Event, Evidence, PrescriptionVersion
from monitoramento_clinico.data.fixtures import write_json
from monitoramento_clinico.replay import load_case, replay
from monitoramento_clinico.vitals import VitalsConfig

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database", type=Path, default=Path("outputs/clinical-demo.db")
    )
    parser.add_argument(
        "--report", type=Path, default=Path("outputs/clinical-demo.json")
    )
    args = parser.parse_args()
    session, samples = load_case(ROOT / "data/fixtures", "development-vitals-2")
    config = VitalsConfig.model_validate_json(
        (ROOT / "configs/vitals.json").read_text()
    )
    monitor = ClinicalMonitor(args.database, config)
    summary = replay(
        monitor, session, samples, speed=0, source_id="synthetic-clinical-demo"
    )
    fixture = ROOT / "data/fixtures/development/development-prescription-3.json"
    for row in json.loads(fixture.read_text())["prescriptions"]:
        monitor.ingest_prescription(PrescriptionVersion.model_validate(row))
    # These are fixture events, not results of Whisper or MediaPipe inference.
    for modality, kind, second in [
        ("text", "critical_mention", 11),
        ("video", "asymmetry", 12),
    ]:
        event = Event(
            event_id=f"synthetic-demo-{modality}",
            patient_id=session.patient_id,
            session_id=session.session_id,
            event_type=kind,
            occurred_at=session.started_at + timedelta(seconds=second),
            ended_at=session.started_at + timedelta(seconds=second + 1),
            processed_at=datetime(2026, 1, 1, tzinfo=UTC),
            detector_version="synthetic-demo-v1",
            evidence=[
                Evidence(
                    source_id=f"synthetic-{modality}",
                    modality=modality,
                    start_seconds=second,
                    end_seconds=second + 1,
                    description="Synthetic fixture event; not a model prediction",
                )
            ],
        )
        monitor.ingest_event(
            event, {"association": "synthetic", "origin": "demo fixture"}
        )
    monitor.set_availability(
        session.session_id,
        session.patient_id,
        "audio",
        "unavailable",
        "Demonstrates independent operation without audio",
    )
    snapshot = monitor.snapshot()
    payload = {
        "scope": "synthetic development demonstration; no clinical validation",
        "cloud_requests": 0,
        "model_inference": False,
        "replay": summary,
        "snapshot": snapshot,
    }
    write_json(args.report, payload)
    print(
        json.dumps(
            {
                "report": str(args.report),
                "events": len(snapshot["events"]),
                "alerts": len(snapshot["alerts"]),
                "combined_alerts": sum(
                    len(a["event_ids"]) > 1 for a in snapshot["alerts"]
                ),
            },
            indent=2,
        )
    )
