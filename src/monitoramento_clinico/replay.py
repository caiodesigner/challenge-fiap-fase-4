"""Reprodução incremental: relógio da captura separado do relógio de execução."""

import json
import math
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from monitoramento_clinico.contracts import Event, Manifest, Measurement, Session
from monitoramento_clinico.data.fixtures import digest
from monitoramento_clinico.data.validation import safe_path
from monitoramento_clinico.vitals import ProcessingResult, VitalsMonitor


def load_case(root: Path, case_id: str) -> tuple[Session, list[Measurement]]:
    manifest = Manifest.model_validate_json((root / "manifest.json").read_text())
    case = next((case for case in manifest.cases if case.case_id == case_id), None)
    if case is None or case.modality != "vitals" or case.input_status != "valid":
        raise ValueError("select a valid vitals case")
    path = safe_path(root, case.path)
    if digest(path) != case.sha256:
        raise ValueError("case checksum mismatch")
    session = next(s for s in manifest.sessions if s.session_id == case.session_id)
    samples = [
        Measurement.model_validate(row)
        for row in json.loads(path.read_text())["measurements"]
    ]
    if not samples:
        raise ValueError("empty case")
    for sample in samples:
        if (sample.patient_id, sample.session_id) != (case.patient_id, case.session_id):
            raise ValueError("sample identity mismatch")
    return session, samples


def _execute_replay(
    monitor: VitalsMonitor,
    session: Session,
    samples: list[Measurement],
    speed: float = 1,
    on_sample: Callable[[Measurement, ProcessingResult], None] | None = None,
) -> dict[str, Any]:
    if not math.isfinite(speed) or speed < 0 or not samples:
        raise ValueError("speed must be nonnegative and samples nonempty")
    monitor.register_session(session)
    started = time.perf_counter()
    first_time = samples[0].occurred_at
    timings: list[float] = []
    onset_latencies: list[float] = []
    schedule_delays: list[float] = []
    statuses: dict[str, int] = {}
    alert_count = 0
    for sample in samples:
        offset = (sample.occurred_at - first_time).total_seconds()
        if speed > 0:
            remaining = offset / speed - (time.perf_counter() - started)
            while remaining > 0:
                time.sleep(min(remaining, 0.1))
                remaining = offset / speed - (time.perf_counter() - started)
        result = monitor.process(sample)
        elapsed = time.perf_counter() - started
        timings.append(result.processing_ms)
        if result.alerts and speed == 1:
            schedule_delays.append(max(0, elapsed - offset))
            # Onset from current event, not historical fixture date versus wall clock.
            events = {
                event["event_id"]: event for event in monitor.snapshot()["events"]
            }
            for alert in result.alerts:
                event = Event.model_validate(events[alert.event_ids[0]])
                onset = (event.occurred_at - first_time).total_seconds()
                onset_latencies.append(elapsed - onset)
        statuses[result.status] = statuses.get(result.status, 0) + 1
        alert_count += len(result.alerts)
        if on_sample is not None:
            on_sample(sample, result)
    ordered = sorted(timings)
    return {
        "mode": "cadence_1x_simulation" if speed == 1 else "accelerated_simulation",
        "speed": speed,
        "samples": len(samples),
        "new_alerts": alert_count,
        "statuses": statuses,
        "elapsed_seconds": time.perf_counter() - started,
        "processing_p95_ms": ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)],
        "confirmation_to_alert_seconds": schedule_delays,
        "confirmation_to_alert_p95_seconds": (
            sorted(schedule_delays)[math.ceil(len(schedule_delays) * 0.95) - 1]
            if schedule_delays
            else None
        ),
        "onset_to_alert_seconds": onset_latencies,
        "realtime_claim": speed == 1,
        "limitation": "Synthetic playback; no sensor or clinical validation",
    }


def replay(
    monitor: VitalsMonitor,
    session: Session,
    samples: list[Measurement],
    speed: float = 1,
    on_sample: Callable[[Measurement, ProcessingResult], None] | None = None,
    source_id: str | None = None,
) -> dict[str, Any]:
    """Registra cada reprodução, mesmo que todas as amostras sejam duplicadas."""
    if not math.isfinite(speed) or speed < 0 or not samples:
        raise ValueError("speed must be nonnegative and samples nonempty")
    monitor.register_session(session)
    run_id = monitor.start_run(session, speed, len(samples), source_id)
    try:
        summary = _execute_replay(monitor, session, samples, speed, on_sample)
    except (Exception, KeyboardInterrupt) as error:
        monitor.finish_run(run_id, None, type(error).__name__)
        raise
    summary["run_id"] = run_id
    monitor.finish_run(run_id, summary)
    return summary
