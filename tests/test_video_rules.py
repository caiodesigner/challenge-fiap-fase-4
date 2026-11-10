import pytest

from monitoramento_clinico.video_rules import (
    PoseFeatures,
    VideoConfig,
    detect_deviations,
    shoulder_angle,
)


def feature(
    second: float, left: float = 0, right: float = 0, y: float = 0.7
) -> PoseFeatures:
    return PoseFeatures(
        time_seconds=second,
        quality="valid",
        left_angle=left,
        right_angle=right,
        center_x=0.5,
        center_y=y,
    )


def test_shoulder_angle_and_degenerate_geometry() -> None:
    assert shoulder_angle((0, 1), (0, 0), (1, 0)) == pytest.approx(90)
    with pytest.raises(ValueError):
        shoulder_angle((0, 0), (0, 0), (1, 0))


def test_symmetric_motion_has_no_deviation() -> None:
    values = list(range(0, 181, 20)) + list(range(160, -1, -20))
    frames = [feature(i * 0.2, angle, angle) for i, angle in enumerate(values)]
    assert detect_deviations(frames, VideoConfig()) == []


def test_persistent_asymmetry_and_short_spike() -> None:
    frames = [feature(i * 0.2, 20, 80) for i in range(10)]
    detected = detect_deviations(frames, VideoConfig())
    assert [d.event_type for d in detected] == ["asymmetry"]
    assert detected[0].start_seconds == 0
    assert detected[0].end_seconds == pytest.approx(1.8)
    assert detect_deviations(frames[:2], VideoConfig()) == []


def test_interruption_requires_prior_motion_and_midrange() -> None:
    frames = [feature(i * 0.2, min(80, i * 20), min(80, i * 20)) for i in range(20)]
    assert any(
        d.event_type == "interruption" for d in detect_deviations(frames, VideoConfig())
    )
    assert (
        detect_deviations([feature(i * 0.2, 80, 80) for i in range(20)], VideoConfig())
        == []
    )


@pytest.mark.parametrize("quality", ["no_person", "multiple_people", "low_confidence"])
def test_quality_issue_breaks_confirmation(quality: str) -> None:
    frames = [
        feature(0, 20, 80),
        feature(0.2, 20, 80),
        PoseFeatures.model_validate({"time_seconds": 0.4, "quality": quality}),
        feature(0.6, 20, 80),
        feature(0.8, 20, 80),
    ]
    assert detect_deviations(frames, VideoConfig()) == []


def test_gap_and_time_ordering() -> None:
    assert (
        detect_deviations([feature(0, 20, 80), feature(10, 20, 80)], VideoConfig())
        == []
    )
    with pytest.raises(ValueError, match="increase"):
        detect_deviations([feature(1), feature(0)], VideoConfig())


def test_rise_candidate_requires_persistence() -> None:
    frames = [feature(0, y=0.8)] + [feature(i * 0.2, y=0.5) for i in range(1, 10)]
    events = detect_deviations(frames, VideoConfig(mode="inpatient"))
    assert [event.event_type for event in events] == ["rise_candidate"]


def test_activity_change_after_active_baseline() -> None:
    frames = [feature(i * 0.2, y=0.7 + (i % 2) * 0.03) for i in range(16)]
    frames += [feature(i * 0.2, y=0.73) for i in range(16, 40)]
    assert any(
        event.event_type == "activity_change"
        for event in detect_deviations(frames, VideoConfig(mode="inpatient"))
    )
