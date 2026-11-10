from pathlib import Path

import pytest

from monitoramento_clinico.contracts import Measurement
from monitoramento_clinico.replay import load_case, replay
from monitoramento_clinico.vitals import VitalsConfig, VitalsMonitor

ROOT = Path(__file__).resolve().parents[1]


def test_each_replay_persists_summary_including_duplicates(tmp_path: Path) -> None:
    config = VitalsConfig.model_validate_json(
        (ROOT / "configs/vitals.json").read_text()
    )
    monitor = VitalsMonitor(tmp_path / "monitor.db", config)
    session, samples = load_case(ROOT / "data/fixtures", "development-vitals-2")
    first = replay(monitor, session, samples, 0, source_id="development-vitals-2")
    second = replay(monitor, session, samples, 0, source_id="development-vitals-2")
    assert first["run_id"] != second["run_id"]
    runs = VitalsMonitor(monitor.path, monitor.config).snapshot()["runs"]
    assert len(runs) == 2
    assert runs[0]["summary"]["statuses"] == {"duplicate": 80}
    assert runs[0]["summary"]["new_alerts"] == 0
    assert runs[1]["summary"]["new_alerts"] == 4
    assert all(run["finished_at"] and run["status"] == "completed" for run in runs)


def test_failed_replay_is_recorded(tmp_path: Path) -> None:
    config = VitalsConfig.model_validate_json(
        (ROOT / "configs/vitals.json").read_text()
    )
    monitor = VitalsMonitor(tmp_path / "monitor.db", config)
    session, samples = load_case(ROOT / "data/fixtures", "development-vitals-1")

    def fail(_sample: Measurement, _result: object) -> None:
        raise RuntimeError("simulated UI interruption")

    with pytest.raises(RuntimeError):
        replay(monitor, session, samples, 0, fail)
    run = monitor.snapshot()["runs"][0]
    assert run["status"] == "failed"
    assert run["error"] == "RuntimeError"
