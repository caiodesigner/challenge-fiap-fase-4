"""Smoke test real do modelo em imagem repetida; não avalia movimento clínico."""

import argparse
import importlib
from pathlib import Path

from monitoramento_clinico.data.fixtures import digest, write_json
from monitoramento_clinico.video import analyze_video

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path, nargs="?")
    parser.add_argument("--blank", action="store_true")
    args = parser.parse_args()
    cv2 = importlib.import_module("cv2")
    if args.blank:
        np = importlib.import_module("numpy")
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
    elif args.image is not None:
        frame = cv2.imread(str(args.image))
    else:
        parser.error("provide image or --blank")
    if frame is None:
        raise ValueError("unreadable image")
    height, width = frame.shape[:2]
    width, height = width // 2 * 2, height // 2 * 2
    frame = cv2.resize(frame, (width, height))
    directory = ROOT / "outputs/video-smoke"
    directory.mkdir(parents=True, exist_ok=True)
    source = directory / ("blank.avi" if args.blank else "static-pose.avi")
    writer = cv2.VideoWriter(
        str(source), cv2.VideoWriter_fourcc(*"MJPG"), 5, (width, height)
    )
    if not writer.isOpened():
        raise ValueError("encoder unavailable")
    try:
        for _ in range(10):
            writer.write(frame)
    finally:
        writer.release()
    report = analyze_video(
        source, directory / "results", ROOT / "models/pose_landmarker_lite.task"
    )
    report["verification_context"] = {
        "construction": "Black frames for two seconds"
        if args.blank
        else "Single image repeated for two seconds; no clinical motion",
        "purpose": "real CPU inference and encoding smoke test only",
        "sample_source_sha256": digest(source) if args.blank else digest(args.image),
    }
    if args.blank:
        assert report["assessment"] == "insufficient" and not report["deviations"]
    write_json(
        ROOT
        / "reports/video"
        / ("no-person-smoke.json" if args.blank else "model-smoke.json"),
        report,
    )
    print(
        {
            key: report[key]
            for key in ("status", "sampled_frames", "quality_counts", "assessment")
        }
    )
