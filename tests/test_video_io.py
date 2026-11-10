import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from monitoramento_clinico.video import analyze_video, extract_features
from monitoramento_clinico.video_rules import VideoConfig


def pose(asymmetric: bool = False) -> list[SimpleNamespace]:
    points = [
        SimpleNamespace(x=0.5, y=0.5, visibility=1, presence=1) for _ in range(33)
    ]
    for index, x, y in [
        (11, 0.4, 0.3),
        (12, 0.6, 0.3),
        (23, 0.4, 0.7),
        (24, 0.6, 0.7),
        (13, 0.2 if asymmetric else 0.4, 0.3 if asymmetric else 0.5),
        (14, 0.6, 0.5),
    ]:
        points[index] = SimpleNamespace(x=x, y=y, visibility=1, presence=1)
    return points


def test_extract_rejects_multiple_or_low_confidence_people() -> None:
    assert extract_features([], 320, 240, 0, VideoConfig()).quality == "no_person"
    assert (
        extract_features([pose(), pose()], 320, 240, 0, VideoConfig()).quality
        == "multiple_people"
    )
    points = pose()
    points[11].visibility = 0.1
    assert (
        extract_features([points], 320, 240, 0, VideoConfig()).quality
        == "low_confidence"
    )


@pytest.mark.parametrize("occlusion", [False, True])
def test_real_video_encoding_with_explicit_test_backend(
    tmp_path: Path, occlusion: bool
) -> None:
    cv2 = pytest.importorskip("cv2")
    np = pytest.importorskip("numpy")
    path = tmp_path / "source.avi"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 5, (320, 240))
    assert writer.isOpened()
    for _ in range(15):
        writer.write(np.zeros((240, 320, 3), dtype=np.uint8))
    writer.release()

    class TestBackend:
        model_id = "explicit-test-backend-not-model-inference"

        def detect(
            self, frame: object, timestamp_ms: int
        ) -> list[list[SimpleNamespace]]:
            if occlusion and timestamp_ms in (0, 400):
                return []
            return [pose(not occlusion)]

        def close(self) -> None:
            pass

    report = analyze_video(
        path, tmp_path / "out", tmp_path / "unused-model", backend=TestBackend()
    )
    assert report["sampled_frames"] == 15
    if occlusion:
        assert report["assessment"] == "partial"
        assert len(report["quality_intervals"]) == 2
        assert report["deviations"] == []
    else:
        assert report["assessment"] == "assessable"
        assert any(event["event_type"] == "asymmetry" for event in report["events"])
    directory = tmp_path / "out" / report["run_id"]
    assert (directory / report["annotated_video"]).stat().st_size > 0
    assert (directory / "report.md").is_file()


def test_invalid_video_leaves_failed_report(tmp_path: Path) -> None:
    pytest.importorskip("cv2")
    path = tmp_path / "broken.mp4"
    path.write_bytes(b"not a video")
    with pytest.raises(ValueError, match="unreadable"):
        analyze_video(path, tmp_path / "out", tmp_path / "unused")
    reports = list((tmp_path / "out").glob("*/report.json"))
    assert len(reports) == 1
    assert json.loads(reports[0].read_text())["status"] == "failed"
