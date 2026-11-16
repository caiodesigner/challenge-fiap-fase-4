from datetime import timedelta

import pytest
from test_clinical_monitor import event, session

from monitoramento_clinico.event_evaluation import (
    alert_volume,
    detection_metrics,
    match_events,
    percentile95,
)


def test_matcher_is_one_to_one_and_ties_are_deterministic() -> None:
    reference = event("reference", "vitals", 10, kind="persistent_deviation")
    a = event("a", "vitals", 15, kind="persistent_deviation")
    b = event("b", "vitals", 5, kind="persistent_deviation")
    result = match_events([b, a], [reference])
    assert result["matches"][0]["prediction_id"] == "a"
    assert result["metrics"] == detection_metrics(1, 1, 0)
    assert match_events([a, b], [reference]) == result


def test_identity_type_and_window_are_required() -> None:
    reference = event("reference", "vitals", 10, kind="persistent_deviation")
    predictions = [
        event("time", "vitals", 16, kind="persistent_deviation"),
        event("class", "vitals", 10, kind="trend_deviation"),
        event(
            "owner", "vitals", 10, session("PAT-SYN-002", "s2"), "persistent_deviation"
        ),
    ]
    assert match_events(predictions, [reference])["metrics"] == detection_metrics(
        0, 3, 1
    )


def test_prescription_matches_by_record_without_time_tolerance() -> None:
    reference = event(
        "same-record", "prescription", 10, kind="unexpected_prescription_change"
    )
    prediction = reference.model_copy(
        update={
            "event_id": "prediction",
            "occurred_at": reference.occurred_at + timedelta(seconds=40),
            "ended_at": reference.ended_at + timedelta(seconds=40),
        }
    )
    assert match_events([prediction], [reference])["metrics"]["true_positive"] == 1
    wrong = event(
        "different-record", "prescription", 10, kind="unexpected_prescription_change"
    )
    assert match_events([wrong], [reference])["metrics"]["true_positive"] == 0


def test_empty_denominators_latency_and_duplicate_identifiers() -> None:
    assert detection_metrics(0, 0, 0)["f1"] is None
    assert detection_metrics(0, 0, 1)["recall"] == 0
    assert percentile95([]) is None
    assert percentile95(list(range(1, 101))) == 95
    with pytest.raises(ValueError, match="nonnegative"):
        percentile95([-1])
    e = event("same", "text", 0)
    with pytest.raises(ValueError, match="duplicate"):
        match_events([e, e], [])
    with pytest.raises(ValueError, match="tolerance"):
        match_events([], [], -1)


def test_fusion_counts_do_not_claim_quality_metrics() -> None:
    assert alert_volume({"events": [], "alerts": []})["alerts_per_event"] is None
    result = alert_volume(
        {
            "events": [1, 2],
            "alerts": [
                {"event_ids": ["a"]},
                {"event_ids": ["b"]},
                {"event_ids": ["a", "b"]},
            ],
        }
    )
    assert result["alerts_per_event"] == 1.5
    assert result["precision_recall_for_fusion"] is None


def test_signal_reference_does_not_match_another_signal() -> None:
    reference = event("reference", "vitals", 10, kind="persistent_deviation")
    reference.evidence[0].signal = "heart_rate"
    wrong = event("wrong", "vitals", 10, kind="persistent_deviation")
    wrong.evidence[0].signal = "spo2"
    assert match_events([wrong], [reference])["metrics"] == detection_metrics(0, 1, 1)
    right = event("right", "vitals", 10, kind="persistent_deviation")
    right.evidence[0].signal = "heart_rate"
    assert match_events([wrong, right], [reference])["metrics"] == detection_metrics(
        1, 1, 0
    )
