"""Confere instalação local e materiais sem publicar ou alterar a entrega."""

import argparse
import importlib.metadata
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inspect_delivery(root: Path) -> dict:
    checks = {}
    for package in (
        "streamlit",
        "faster-whisper",
        "mediapipe",
        "opencv-contrib-python",
    ):
        try:
            checks[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            checks[package] = None
    models = {
        name: (root / "models" / name).is_file()
        for name in ("pose_landmarker_lite.task", "faster-whisper-small/model.bin")
    }
    delivery = json.loads((root / "docs/entrega.json").read_text())
    pending = []
    if not delivery.get("author_or_team"):
        pending.append("Preencher autor/equipe")
    if not delivery.get("release_commit"):
        pending.append("Registrar commit final publicado")
    video = delivery["video"]
    if not video.get("url") or not video.get("public_access_checked"):
        pending.append("Gravar/publicar vídeo e conferir acesso público")
    duration = video.get("duration_seconds")
    if not isinstance(duration, (int, float)) or not 0 < duration <= 900:
        pending.append("Conferir duração do vídeo: 1 a 900 segundos")
    for field in ("representative_media_complete", "independent_test_complete"):
        if not delivery["evaluation"].get(field):
            pending.append(field)
    return {
        "dependencies": checks,
        "models": models,
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "local_execution_ready": all(checks.values()) and all(models.values()),
        "submission_ready": not pending,
        "pending": pending,
        "scope": "installation and declared delivery metadata; not accuracy validation",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-submission", action="store_true")
    args = parser.parse_args()
    result = inspect_delivery(ROOT)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(
        0
        if result[
            "submission_ready" if args.require_submission else "local_execution_ready"
        ]
        else 1
    )
