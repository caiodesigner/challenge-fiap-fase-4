"""Transcrição Whisper exclusivamente local, sem download implícito na análise."""

import importlib
import os
from functools import lru_cache
from pathlib import Path
from time import perf_counter
from typing import Any, Literal

from monitoramento_clinico.data.fixtures import digest


def local_gpu_count() -> int:
    try:
        return int(importlib.import_module("ctranslate2").get_cuda_device_count())
    except (ImportError, RuntimeError):
        return 0


@lru_cache(maxsize=1)
def load_model(path: str, device: str) -> Any:
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    importlib.import_module("onnxruntime").disable_telemetry_events()
    module = importlib.import_module("faster_whisper")
    return module.WhisperModel(
        path,
        device=device,
        compute_type="int8" if device == "cpu" else "int8_float16",
        local_files_only=True,
        cpu_threads=4,
    )


class LocalSpeechClient:
    def __init__(
        self,
        model_path: Path,
        device: Literal["cpu", "cuda"] = "cpu",
        language: str = "pt",
    ) -> None:
        self.model_path = model_path.resolve()
        self.device = device
        self.language = language

    def transcribe(self, audio: Path) -> dict[str, Any]:
        if not (self.model_path / "model.bin").is_file():
            raise ValueError("local model missing; run scripts/prepare_local_speech.py")
        if self.device == "cuda" and local_gpu_count() == 0:
            raise ValueError("CUDA GPU is not accessible; select CPU")
        started = perf_counter()
        model = load_model(str(self.model_path), self.device)
        segments, info = model.transcribe(
            str(audio),
            language=self.language,
            beam_size=5,
            vad_filter=True,
            word_timestamps=True,
            condition_on_previous_text=False,
        )
        results = []
        for segment in segments:
            results.append(
                {
                    "start_seconds": float(segment.start),
                    "end_seconds": float(segment.end),
                    "text": segment.text.strip(),
                    "words": [
                        {
                            "start_seconds": float(word.start),
                            "end_seconds": float(word.end),
                            "text": word.word,
                            "probability": float(word.probability),
                        }
                        for word in (segment.words or [])
                    ],
                }
            )
        text = " ".join(segment["text"] for segment in results).strip()
        return {
            "status": "completed" if text else "no_match",
            "text": text,
            "segments": results,
            "language": info.language,
            "device": self.device,
            "compute_type": "int8" if self.device == "cpu" else "int8_float16",
            "model_path": self.model_path.name,
            "model_sha256": digest(self.model_path / "model.bin"),
            "elapsed_seconds": perf_counter() - started,
            "network_used": False,
            "manual_review_required": True,
            "recognition_quality_validated": False,
        }
