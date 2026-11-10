"""CLI para análise postural e relatório automático."""

import argparse
import json
from pathlib import Path

from monitoramento_clinico.video import analyze_video
from monitoramento_clinico.video_rules import VideoConfig

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument(
        "--model", type=Path, default=Path("models/pose_landmarker_lite.task")
    )
    parser.add_argument("--output", type=Path, default=Path("outputs/video"))
    parser.add_argument(
        "--mode", choices=["rehabilitation", "inpatient"], default="rehabilitation"
    )
    args = parser.parse_args()
    result = analyze_video(
        args.video, args.output, args.model, VideoConfig(mode=args.mode)
    )
    print(
        json.dumps(
            {key: value for key, value in result.items() if key != "features"}, indent=2
        )
    )
