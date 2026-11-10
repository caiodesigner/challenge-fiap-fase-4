"""Verifica Whisper e MediaPipe em CPU sem usar APIs externas."""

import argparse
import importlib
import importlib.metadata
from pathlib import Path

from monitoramento_clinico.audio import analyze_audio
from monitoramento_clinico.data.fixtures import write_json
from monitoramento_clinico.local_speech import LocalSpeechClient, local_gpu_count
from monitoramento_clinico.video import MediaPipeBackend

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("audio", type=Path)
    parser.add_argument("--language", default="pt")
    args = parser.parse_args()
    speech = analyze_audio(
        args.audio,
        ROOT / "outputs/local-installation/reports",
        use_whisper=True,
        local_client=LocalSpeechClient(
            ROOT / "models/faster-whisper-small", language=args.language
        ),
    )
    assert speech["status"] == "completed" and speech["transcript"]
    assert speech["cloud_request_count"] == 0
    np = importlib.import_module("numpy")
    backend = MediaPipeBackend(ROOT / "models/pose_landmarker_lite.task")
    try:
        poses = backend.detect(np.zeros((240, 320, 3), dtype=np.uint8), 0)
        assert not poses
    finally:
        backend.close()
    result = {
        "scope": "local installation smoke test; not clinical or accuracy validation",
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("faster-whisper", "ctranslate2", "av", "mediapipe")
        },
        "cuda_devices_visible": local_gpu_count(),
        "execution_device": "cpu",
        "whisper": {
            "status": speech["status"],
            "language": args.language,
            "compute_type": speech["local_speech"]["compute_type"],
            "elapsed_seconds": speech["local_speech"]["elapsed_seconds"],
            "transcript_characters": len(speech["transcript"]),
            "model_sha256": speech["local_speech"]["model_sha256"],
            "audio_sha256": speech["source_sha256"],
        },
        "mediapipe": {
            "status": "passed",
            "blank_frame_people": len(poses),
            "model_id": backend.model_id,
        },
        "azure_requests": 0,
        "offline_model_loading": True,
    }
    write_json(ROOT / "reports/validation/local-stack.json", result)
    print(result)
