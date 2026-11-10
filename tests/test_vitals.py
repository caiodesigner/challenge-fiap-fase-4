import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from monitoramento_clinico.contracts import Measurement, Session
from monitoramento_clinico.replay import load_case, replay
from monitoramento_clinico.vitals import VitalsConfig, VitalsMonitor

ROOT = Path(__file__).resolve().parents[1]
START = datetime(2026, 1, 1, tzinfo=UTC)


def sample(second: int, value: float = 130, **changes: object) -> Measurement:
    payload = {
        "record_id": f"sample-{second}",
        "patient_id": "PAT-SYN-001",
        "session_id": "session-1",
        "occurred_at": START + timedelta(seconds=second),
        "ingested_at": START + timedelta(seconds=second),
        "signal": "heart_rate",
        "value": value,
        "unit": "bpm",
        **changes,
    }
    return Measurement.model_validate(payload)


@pytest.fixture
def monitor(tmp_path: Path) -> VitalsMonitor:
    config = VitalsConfig.model_validate_json(
        (ROOT / "configs/vitals.json").read_text()
    )
    monitor = VitalsMonitor(tmp_path / "monitor.db", config)
    monitor.register_session(
        Session(
            session_id="session-1",
            patient_id="PAT-SYN-001",
            started_at=START,
            ended_at=START + timedelta(seconds=60),
        )
    )
    return monitor


def test_persistent_episode_emits_once_and_survives_restart(
    monitor: VitalsMonitor,
) -> None:
    for second in range(3):
        assert monitor.process(sample(second)).alerts == []
    restarted = VitalsMonitor(monitor.path, monitor.config)
    result = restarted.process(sample(3))
    assert len(result.alerts) == 1
    assert result.processing_ms >= 0
    for second in range(4, 10):
        assert restarted.process(sample(second)).alerts == []
    assert restarted.process(sample(3)).status == "duplicate"
    assert len(restarted.snapshot()["alerts"]) == 1


def test_recovery_allows_new_episode(monitor: VitalsMonitor) -> None:
    for second in range(4):
        monitor.process(sample(second))
    monitor.process(sample(4, 75))
    for second in range(5, 9):
        monitor.process(sample(second))
    assert len(monitor.snapshot()["alerts"]) == 2


def test_artifact_and_gap_reset_persistence(monitor: VitalsMonitor) -> None:
    monitor.process(sample(0))
    monitor.process(sample(1, quality="artifact"))
    monitor.process(sample(2))
    assert monitor.process(sample(4)).alerts == []
    assert monitor.process(sample(8)).alerts == []
    assert monitor.snapshot()["alerts"] == []


def test_out_of_order_and_conflicting_records(monitor: VitalsMonitor) -> None:
    monitor.process(sample(2))
    assert monitor.process(sample(1)).status == "out_of_order"
    with pytest.raises(ValueError, match="conflict"):
        monitor.process(sample(2, 80))
    assert len(monitor.snapshot()["samples"]) == 2


def test_patient_and_session_boundaries(monitor: VitalsMonitor) -> None:
    with pytest.raises(ValueError, match="own session"):
        monitor.process(sample(0, patient_id="PAT-SYN-002"))
    with pytest.raises(ValueError, match="outside session"):
        monitor.process(sample(70))
    with pytest.raises(ValueError, match="unknown session"):
        monitor.process(sample(0, session_id="unknown"))
    assert monitor.snapshot()["samples"] == []


def test_review_transitions_and_history(monitor: VitalsMonitor) -> None:
    for second in range(4):
        monitor.process(sample(second))
    identifier = monitor.snapshot()["alerts"][0]["alert_id"]
    with pytest.raises(ValueError, match="transition"):
        monitor.review_alert(identifier, "close", "demo", "check", "confirmed")
    acknowledged = monitor.review_alert(identifier, "acknowledge", "demo", "seen")
    assert acknowledged.status == "acknowledged"
    closed = monitor.review_alert(identifier, "close", "demo", "reviewed", "confirmed")
    assert closed.status == "closed"
    restored = VitalsMonitor(monitor.path, monitor.config).snapshot()
    assert restored["alerts"][0]["review"] == "confirmed"
    assert [row["action"] for row in restored["history"]] == ["acknowledge", "close"]


def test_failed_alert_transaction_rolls_back_sample_and_state(
    monitor: VitalsMonitor,
) -> None:
    for second in range(3):
        monitor.process(sample(second))
    with sqlite3.connect(monitor.path) as connection:
        connection.executescript("""
            CREATE TRIGGER fail_alert BEFORE INSERT ON monitoring_alerts
            BEGIN SELECT RAISE(ABORT, 'simulated failure'); END;
        """)
    with pytest.raises(sqlite3.IntegrityError):
        monitor.process(sample(3))
    snapshot = monitor.snapshot()
    assert len(snapshot["samples"]) == 3
    assert snapshot["events"] == []
    with sqlite3.connect(monitor.path) as connection:
        connection.execute("DROP TRIGGER fail_alert")
    assert len(monitor.process(sample(3)).alerts) == 1


def test_two_patients_do_not_share_persistence_state(monitor: VitalsMonitor) -> None:
    monitor.register_session(
        Session(
            session_id="session-2",
            patient_id="PAT-SYN-002",
            started_at=START,
            ended_at=START + timedelta(seconds=60),
        )
    )
    for second in range(2):
        monitor.process(sample(second))
        monitor.process(
            sample(second, session_id="session-2", patient_id="PAT-SYN-002")
        )
    assert monitor.snapshot()["alerts"] == []
    for second in range(2, 4):
        monitor.process(sample(second))
    assert {alert["patient_id"] for alert in monitor.snapshot()["alerts"]} == {
        "PAT-SYN-001"
    }


@pytest.mark.parametrize("variant,expected", [(1, 0), (2, 4), (4, 0)])
def test_full_fixture_replay_and_deduplication(
    monitor: VitalsMonitor, variant: int, expected: int
) -> None:
    session, samples = load_case(
        ROOT / "data/fixtures", f"development-vitals-{variant}"
    )
    report = replay(monitor, session, samples, speed=0)
    assert report["new_alerts"] == expected
    assert report["realtime_claim"] is False
    repeated = replay(monitor, session, samples, speed=0)
    assert repeated["statuses"] == {"duplicate": 80}
    assert len(monitor.snapshot()["alerts"]) == expected
