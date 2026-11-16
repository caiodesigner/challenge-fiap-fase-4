import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
evaluate = runpy.run_path(str(ROOT / "scripts/evaluate_video.py"))["evaluate"]


def test_video_reference_identity_and_negative_case(tmp_path: Path) -> None:
    report = ROOT / "reports/video/model-smoke.json"
    payload = json.loads(report.read_text())
    reference = tmp_path / "manual.json"
    manual = {
        "source_sha256": payload["source_sha256"],
        "mode": "rehabilitation",
        "annotator": "independent-reviewer",
        "source_group": "staged-source-1",
        "labels": [],
    }
    reference.write_text(json.dumps(manual))
    result = evaluate(report, reference)
    assert result["comparison"]["metrics"]["false_positive"] == 0
    assert result["comparison"]["metrics"]["recall"] is None
    manual["source_sha256"] = "wrong-source"
    reference.write_text(json.dumps(manual))
    with pytest.raises(ValueError, match="checksum"):
        evaluate(report, reference)


def test_video_manual_label_is_counted_as_miss(tmp_path: Path) -> None:
    report = ROOT / "reports/video/model-smoke.json"
    payload = json.loads(report.read_text())
    reference = tmp_path / "manual.json"
    reference.write_text(
        json.dumps(
            {
                "source_sha256": payload["source_sha256"],
                "mode": "rehabilitation",
                "annotator": "reviewer",
                "source_group": "source-1",
                "labels": [
                    {
                        "event_type": "asymmetry",
                        "start_seconds": 0,
                        "end_seconds": 1,
                        "basis": "manual_annotation",
                    }
                ],
            }
        )
    )
    assert evaluate(report, reference)["comparison"]["metrics"]["false_negative"] == 1
