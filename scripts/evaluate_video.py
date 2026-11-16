"""Avalia relatório de vídeo contra intervalos manuais separados da inferência."""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

from monitoramento_clinico.contracts import Event, Evidence, ReferenceLabel
from monitoramento_clinico.data.fixtures import digest, write_json
from monitoramento_clinico.event_evaluation import match_events


def evaluate(report_path: Path, reference_path: Path) -> dict:
    report = json.loads(report_path.read_text())
    reference = json.loads(reference_path.read_text())
    if report["status"] != "completed" or report.get("assessment") != "assessable":
        raise ValueError("video must be completed and assessable")
    if reference["source_sha256"] != report["source_sha256"]:
        raise ValueError("reference source checksum mismatch")
    if reference["mode"] != report["config"]["mode"]:
        raise ValueError("reference mode mismatch")
    if not reference.get("annotator") or not reference.get("source_group"):
        raise ValueError("annotator and source group required")
    origin = datetime.fromisoformat(report["started_at"])
    predictions = [Event.model_validate(e) for e in report["events"]]
    references = []
    for index, raw in enumerate(reference["labels"]):
        label = ReferenceLabel.model_validate(raw)
        if label.basis != "manual_annotation":
            raise ValueError("manual references required")
        if label.end_seconds > report["duration_seconds"]:
            raise ValueError("reference outside video duration")
        references.append(
            Event(
                event_id=f"manual-{index}",
                patient_id=report["patient_id"],
                session_id=report["session_id"],
                event_type=label.event_type,
                occurred_at=origin + timedelta(seconds=label.start_seconds),
                ended_at=origin + timedelta(seconds=label.end_seconds),
                processed_at=origin,
                detector_version="manual-reference-v1",
                evidence=[
                    Evidence(
                        source_id=report["source_sha256"],
                        modality="video",
                        start_seconds=label.start_seconds,
                        end_seconds=label.end_seconds,
                        description=f"Manual annotation: {reference['annotator']}",
                    )
                ],
            )
        )
    return {
        "comparison": match_events(predictions, references),
        "report_sha256": digest(report_path),
        "reference_sha256": digest(reference_path),
        "source_group": reference["source_group"],
        "clinical_validation": False,
        "limitation": "One annotated recording; does not establish generalization",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/evaluation/video.json")
    )
    args = parser.parse_args()
    result = evaluate(args.report, args.reference)
    write_json(args.output, result)
    print(json.dumps(result, indent=2))
