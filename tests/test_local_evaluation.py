import json
from pathlib import Path

import pytest

from monitoramento_clinico.local_evaluation import evaluate_local_fixtures
from monitoramento_clinico.vitals import VitalsConfig

ROOT = Path(__file__).resolve().parents[1]


def evaluate(case: str | None = None) -> dict:
    return evaluate_local_fixtures(
        ROOT / "data/fixtures",
        VitalsConfig.model_validate_json((ROOT / "configs/vitals.json").read_text()),
        json.loads((ROOT / "configs/evaluation.json").read_text()),
        case_id=case,
    )


def test_paired_variants_use_same_inputs_and_separate_databases() -> None:
    report = evaluate("development-vitals-2")
    first, second = report["cases"]
    assert first["input_sha256"] == second["input_sha256"]
    assert first["references"] == second["references"]
    assert first["detector_config"]["persistence_seconds"] == 0
    assert second["detector_config"]["persistence_seconds"] == 3
    assert report["summaries"]["temporal"]["confirmation_to_alert_p95_seconds"] is None
    assert report["cases"][0]["status"] == "completed"


def test_invalid_input_and_unlabelled_quality_events_are_explicit() -> None:
    rejected = evaluate("development-vitals-5")
    assert all(row["status"] == "rejected_invalid_input" for row in rejected["cases"])
    assert rejected["summaries"]["temporal"]["metrics"]["precision"] is None
    quality = evaluate("development-prescription-4")["cases"][0]
    assert quality["predictions"] == []
    assert quality["unscored_events"][0]["event_type"] == "prescription_unit_issue"
    assert quality["comparison"]["metrics"]["f1"] is None


def test_missing_case_fails_instead_of_reporting_success() -> None:
    with pytest.raises(ValueError, match="no supported cases"):
        evaluate("not-a-case")


def test_instant_baseline_emits_at_onset_and_temporal_waits() -> None:
    report = evaluate("development-vitals-2")
    first, second = report["cases"]
    from datetime import datetime

    for row, expected_seconds in [(first, 0), (second, 3)]:
        assert row["predictions"]
        for prediction in row["predictions"]:
            delta = datetime.fromisoformat(
                prediction["ended_at"]
            ) - datetime.fromisoformat(prediction["occurred_at"])
            assert delta.total_seconds() == expected_seconds


def test_trend_miss_is_exposed_by_class() -> None:
    report = evaluate("development-vitals-3")
    for row in report["cases"]:
        assert (
            row["comparison"]["by_event_type"]["trend_deviation"]["false_negative"] == 1
        )
