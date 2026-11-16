"""Pareamento um a um e métricas por evento, com denominadores explícitos."""

import math
from typing import Any

from monitoramento_clinico.contracts import Event


def percentile95(values: list[float]) -> float | None:
    if any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("latency values must be finite and nonnegative")
    return sorted(values)[math.ceil(len(values) * 0.95) - 1] if values else None


def detection_metrics(tp: int, fp: int, fn: int) -> dict[str, Any]:
    if min(tp, fp, fn) < 0:
        raise ValueError("event counts cannot be negative")
    return {
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
    }


def match_events(
    predictions: list[Event], references: list[Event], tolerance_seconds: float = 5
) -> dict[str, Any]:
    """Menor distância global, desempate por ID; texto/prescrição por origem."""
    if not math.isfinite(tolerance_seconds) or tolerance_seconds < 0:
        raise ValueError("invalid onset tolerance")
    for collection in (predictions, references):
        if len({event.event_id for event in collection}) != len(collection):
            raise ValueError("duplicate event identifier in evaluation input")
    candidates = []
    for prediction in predictions:
        for reference in references:
            if (
                prediction.patient_id,
                prediction.session_id,
                prediction.event_type,
            ) != (reference.patient_id, reference.session_id, reference.event_type):
                continue
            expected_signals = {e.signal for e in reference.evidence if e.signal}
            if expected_signals and expected_signals != {
                e.signal for e in prediction.evidence if e.signal
            }:
                continue
            source_match = any(
                e.modality in {"text", "prescription"} for e in reference.evidence
            )
            distance = abs(
                (prediction.occurred_at - reference.occurred_at).total_seconds()
            )
            if source_match:
                expected = {e.source_id for e in reference.evidence}
                if not expected.intersection(e.source_id for e in prediction.evidence):
                    continue
                distance = 0  # No temporal tolerance for source-record matching.
            elif distance > tolerance_seconds:
                continue
            candidates.append((distance, prediction.event_id, reference.event_id))
    used_predictions: set[str] = set()
    used_references: set[str] = set()
    matches = []
    for distance, prediction_id, reference_id in sorted(candidates):
        if prediction_id in used_predictions or reference_id in used_references:
            continue
        used_predictions.add(prediction_id)
        used_references.add(reference_id)
        matches.append(
            {
                "prediction_id": prediction_id,
                "reference_id": reference_id,
                "distance_seconds": distance,
            }
        )
    unmatched_predictions = sorted(
        e.event_id for e in predictions if e.event_id not in used_predictions
    )
    unmatched_references = sorted(
        e.event_id for e in references if e.event_id not in used_references
    )
    types = sorted({e.event_type for e in predictions + references})
    by_type = {
        kind: detection_metrics(
            sum(
                e.event_type == kind and e.event_id in used_predictions
                for e in predictions
            ),
            sum(
                e.event_type == kind and e.event_id not in used_predictions
                for e in predictions
            ),
            sum(
                e.event_type == kind and e.event_id not in used_references
                for e in references
            ),
        )
        for kind in types
    }
    return {
        "metrics": detection_metrics(
            len(matches), len(unmatched_predictions), len(unmatched_references)
        ),
        "matches": matches,
        "unmatched_predictions": unmatched_predictions,
        "unmatched_references": unmatched_references,
        "by_event_type": by_type,
    }


def alert_volume(snapshot: dict[str, Any]) -> dict[str, Any]:
    isolated = sum(len(a["event_ids"]) == 1 for a in snapshot["alerts"])
    combined = len(snapshot["alerts"]) - isolated
    return {
        "events": len(snapshot["events"]),
        "isolated_alerts": isolated,
        "combined_alerts": combined,
        "total_alerts": isolated + combined,
        "alerts_per_event": (isolated + combined) / len(snapshot["events"])
        if snapshot["events"]
        else None,
        "precision_recall_for_fusion": None,
        "limitation": (
            "No independent multimodal reference labels; "
            "counts do not measure detection quality"
        ),
    }
