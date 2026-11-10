"""Download explícito do modelo oficial; pesos ficam fora do Git."""

import json
import urllib.request
from pathlib import Path

from monitoramento_clinico.data.fixtures import digest

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a"
URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)


if __name__ == "__main__":
    path = ROOT / "models/pose_landmarker_lite.task"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with urllib.request.urlopen(URL, timeout=60) as response:
            content = response.read()
        temporary = path.with_suffix(".tmp")
        temporary.write_bytes(content)
        if digest(temporary) != EXPECTED_SHA256:
            raise ValueError("downloaded model checksum mismatch")
        temporary.replace(path)
    if digest(path) != EXPECTED_SHA256:
        raise ValueError("existing model checksum mismatch; inspect local weights")
    manifest = {
        "url": URL,
        "sha256": digest(path),
        "upstream_version": "float16/1",
        "documentation": "https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker",
        "distribution": "weights downloaded separately; not included in repository",
    }
    (path.parent / "pose-model-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    print(json.dumps(manifest, indent=2))
