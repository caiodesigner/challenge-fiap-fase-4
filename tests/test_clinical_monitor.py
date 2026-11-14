import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from monitoramento_clinico.clinical_monitor import ClinicalMonitor
from monitoramento_clinico.contracts import (
    Event,
    Evidence,
    PrescriptionVersion,
    Session,
)
from monitoramento_clinico.replay import load_case, replay
from monitoramento_clinico.vitals import VitalsConfig

ROOT = Path(__file__).resolve().parents[1]
START = datetime(2026, 1, 1, tzinfo=UTC)


def session(patient: str = "PAT-SYN-001", identity: str = "s1") -> Session:
    return Session(
        session_id=identity,
        patient_id=patient,
        started_at=START,
        ended_at=START + timedelta(minutes=5),
    )


def monitor(tmp_path: Path) -> ClinicalMonitor:
    result = ClinicalMonitor(
        tmp_path / "clinical.db",
        VitalsConfig.model_validate_json((ROOT / "configs/vitals.json").read_text()),
    )
    result.register_session(session())
    return result


def event(
    identity: str,
    modality: str,
    second: float,
    owner: Session | None = None,
    kind: str = "critical_mention",
) -> Event:
    owner = owner or session()
    instant = START + timedelta(seconds=second)
    return Event(
        event_id=identity,
        patient_id=owner.patient_id,
        session_id=owner.session_id,
        event_type=kind,
        occurred_at=instant,
        ended_at=instant,
        processed_at=START,
        detector_version="test-v1",
        evidence=[
            Evidence(
                source_id=identity,
                modality=modality,
                start_seconds=second,
                end_seconds=second,
                description="synthetic evidence",
            )
        ],
    )


def prescription(
    identity: str, second: float, dose: float | None = 1, **kwargs: object
) -> PrescriptionVersion:
    return PrescriptionVersion.model_validate(
        dict(
            record_id=identity,
            patient_id="PAT-SYN-001",
            session_id="s1",
            medication_id="SYNTHETIC-A",
            occurred_at=START + timedelta(seconds=second),
            dose=dose,
            unit="synthetic_unit",
            action="start",
            **kwargs,
        )
    )


@pytest.mark.parametrize(
    "case,kind",
    [
        (1, None),
        (2, None),
        (3, "unexpected_prescription_change"),
        (4, "prescription_unit_issue"),
        (5, "unexpected_prescription_stop"),
    ],
)
def test_prescription_scenarios_and_restart(
    tmp_path: Path, case: int, kind: str | None
) -> None:
    m = monitor(tmp_path)
    payload = json.loads(
        (
            ROOT / f"data/fixtures/development/development-prescription-{case}.json"
        ).read_text()
    )
    rows = [
        PrescriptionVersion.model_validate({**r, "session_id": "s1"})
        for r in payload["prescriptions"]
    ]
    for row in rows:
        m.ingest_prescription(row)
    before = m.snapshot()
    assert [e["event_type"] for e in before["events"]] == ([kind] if kind else [])
    assert len(before["prescriptions"]) == (3 if case == 5 else 2)
    for row in rows:
        assert monitor(tmp_path).ingest_prescription(row)["status"] == "duplicate"
    assert m.snapshot()["alerts"] == before["alerts"]
    if case == 4:
        assert before["alerts"][0]["severity"] == "observation"


def test_out_of_order_and_conflicting_prescription_do_not_corrupt_state(
    tmp_path: Path,
) -> None:
    m = monitor(tmp_path)
    first = prescription("first", 10)
    m.ingest_prescription(first)
    old = first.model_copy(update={"record_id": "old", "occurred_at": START})
    assert m.ingest_prescription(old)["status"] == "out_of_order"
    with pytest.raises(ValueError, match="conflict"):
        m.ingest_prescription(first.model_copy(update={"dose": 2}))
    change = first.model_copy(
        update={
            "record_id": "change",
            "occurred_at": START + timedelta(seconds=20),
            "action": "change",
            "dose": 4,
        }
    )
    assert (
        m.ingest_prescription(change)["event_type"] == "unexpected_prescription_change"
    )


def test_invalid_sequence_is_visible_but_not_correlated_as_clinical_event(
    tmp_path: Path,
) -> None:
    m = monitor(tmp_path)
    row = prescription("first", 10).model_copy(update={"action": "change"})
    assert m.ingest_prescription(row)["status"] == "invalid_transition"
    m.ingest_event(event("voice", "text", 10))
    assert all(len(a["event_ids"]) == 1 for a in m.snapshot()["alerts"])


def test_late_events_correlate_at_window_boundary_and_deduplicate(
    tmp_path: Path,
) -> None:
    m = monitor(tmp_path)
    m.ingest_event(event("late", "video", 40, kind="asymmetry"))
    alerts = m.ingest_event(event("early", "text", 10))
    assert [a.severity for a in alerts] == ["attention", "priority"]
    assert monitor(tmp_path).ingest_event(event("early", "text", 10)) == []
    fused = next(a for a in m.snapshot()["alerts"] if len(a["event_ids"]) == 2)
    m.review_alert(fused["alert_id"], "acknowledge", "tester", "reviewed")
    m.review_alert(fused["alert_id"], "close", "tester", "reviewed", "confirmed")
    m.ingest_event(event("late", "video", 40, kind="asymmetry"))
    assert (
        next(a for a in m.snapshot()["alerts"] if a["alert_id"] == fused["alert_id"])[
            "status"
        ]
        == "closed"
    )


@pytest.mark.parametrize(
    "modality,second,owner",
    [
        ("audio", 10, session()),
        ("video", 41, session()),
        ("video", 10, session("PAT-SYN-002", "s2")),
        ("video", 10, session(identity="s3")),
    ],
)
def test_dependent_sources_distant_times_and_other_identities_do_not_fuse(
    tmp_path: Path, modality: str, second: float, owner: Session
) -> None:
    m = monitor(tmp_path)
    m.register_session(owner)
    m.ingest_event(event("first", "text", 10))
    m.ingest_event(event("second", modality, second, owner))
    assert all(len(a["event_ids"]) == 1 for a in m.snapshot()["alerts"])


def test_unknown_patient_and_interval_rejected_atomically(tmp_path: Path) -> None:
    m = monitor(tmp_path)
    with pytest.raises(ValueError, match="patient"):
        m.ingest_event(event("bad", "text", 5, session("PAT-SYN-002")))
    with pytest.raises(ValueError, match="outside"):
        m.ingest_event(event("bad", "text", 301))
    assert m.snapshot()["events"] == []


def test_unavailable_modality_does_not_block_independent_alert(tmp_path: Path) -> None:
    m = monitor(tmp_path)
    m.set_availability(
        "s1", "PAT-SYN-001", "video", "unavailable", "camera disconnected"
    )
    assert m.ingest_event(event("voice", "text", 5))[0].severity == "attention"
    assert m.snapshot()["availability"][0]["status"] == "unavailable"


def test_vitals_events_and_prescription_are_integrated(tmp_path: Path) -> None:
    m = monitor(tmp_path)
    owner, samples = load_case(ROOT / "data/fixtures", "development-vitals-2")
    replay(m, owner, samples, speed=0)
    instant = max(
        datetime.fromisoformat(e["occurred_at"]) for e in m.snapshot()["events"]
    )
    e = event("voice", "text", (instant - START).total_seconds(), owner)
    m.ingest_event(e)
    before = m.snapshot()
    assert any(len(a["event_ids"]) == 2 for a in before["alerts"])
    replay(m, owner, samples, speed=0)
    assert m.snapshot()["alerts"] == before["alerts"]


def test_config_change_requires_separate_database(tmp_path: Path) -> None:
    from monitoramento_clinico.clinical_monitor import ClinicalConfig

    m = monitor(tmp_path)
    with pytest.raises(ValueError, match="config changed"):
        ClinicalMonitor(m.path, m.config, ClinicalConfig(fusion_window_seconds=60))
