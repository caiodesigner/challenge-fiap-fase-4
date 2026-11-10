"""Medidas acústicas locais de WAV PCM; atividade por energia não é diagnóstico."""

import array
import math
import sys
import wave
from pathlib import Path
from typing import Any

from pydantic import Field

from monitoramento_clinico.contracts import Contract


class AcousticConfig(Contract):
    version: str = "energy-pauses-v1"
    max_duration_seconds: float = Field(default=30, gt=0, le=60)
    frame_ms: int = Field(default=20, ge=10, le=100)
    silence_dbfs: float = Field(default=-55, ge=-100, le=-20)
    minimum_pause_seconds: float = Field(default=0.5, gt=0)
    long_pause_seconds: float = Field(default=2, gt=0)


def analyze_acoustics(
    path: Path, config: AcousticConfig | None = None
) -> dict[str, Any]:
    config = config or AcousticConfig()
    if not path.is_file() or path.stat().st_size > 4 * 1024**2:
        raise ValueError("missing audio or file exceeds 4 MB")
    try:
        with wave.open(str(path), "rb") as audio:
            if (
                audio.getnchannels(),
                audio.getsampwidth(),
                audio.getframerate(),
                audio.getcomptype(),
            ) != (1, 2, 16000, "NONE"):
                raise ValueError("audio must be mono 16-bit PCM WAV at 16000 Hz")
            count = audio.getnframes()
            duration = count / 16000
            if not 0.3 <= duration <= config.max_duration_seconds:
                raise ValueError("audio duration outside configured range")
            raw = audio.readframes(count)
            if len(raw) != count * 2:
                raise ValueError("truncated WAV")
    except (wave.Error, EOFError) as error:
        raise ValueError("invalid PCM WAV") from error
    samples = array.array("h", raw)
    if sys.byteorder != "little":
        samples.byteswap()
    window = int(16000 * config.frame_ms / 1000)
    frames: list[dict[str, Any]] = []
    for offset in range(0, len(samples), window):
        segment = samples[offset : offset + window]
        rms = (
            math.sqrt(sum(float(value) ** 2 for value in segment) / len(segment))
            / 32768
        )
        frames.append(
            {
                "start_seconds": offset / 16000,
                "end_seconds": (offset + len(segment)) / 16000,
                "rms_dbfs": max(-100, 20 * math.log10(max(rms, 1e-5))),
            }
        )
    rms = math.sqrt(sum(float(value) ** 2 for value in samples) / len(samples)) / 32768
    overall = max(-100, 20 * math.log10(max(rms, 1e-5)))
    clipping = sum(abs(value) >= 32760 for value in samples) / len(samples)
    quality = (
        "silence"
        if overall < config.silence_dbfs
        else (
            "clipped"
            if clipping > 0.01
            else "low_signal"
            if overall < -45
            else "assessable"
        )
    )
    threshold = max(-50, max(frame["rms_dbfs"] for frame in frames) - 35)
    active = [frame["rms_dbfs"] > threshold for frame in frames]
    pauses: list[dict[str, float]] = []
    active_indices = [index for index, value in enumerate(active) if value]
    if active_indices:
        start: float | None = None
        for index in range(active_indices[0], active_indices[-1] + 1):
            if not active[index] and start is None:
                start = frames[index]["start_seconds"]
            if active[index] and start is not None:
                end = frames[index]["start_seconds"]
                if end - start >= config.minimum_pause_seconds - 1e-8:
                    pauses.append(
                        {
                            "start_seconds": start,
                            "end_seconds": end,
                            "duration_seconds": end - start,
                        }
                    )
                start = None
    return {
        "config": config.model_dump(),
        "sample_rate": 16000,
        "duration_seconds": duration,
        "quality": quality,
        "rms_dbfs": overall,
        "clipping_ratio": clipping,
        "energy_activity_ratio": sum(active) / len(active),
        "zero_crossing_rate": sum(
            (a < 0) != (b < 0) for a, b in zip(samples, samples[1:], strict=False)
        )
        / max(1, len(samples) - 1),
        "internal_pauses": pauses,
        "longest_internal_pause_seconds": max(
            (p["duration_seconds"] for p in pauses), default=0
        ),
        "frames": frames,
        "limitation": "Energy activity is not speech detection or clinical diagnosis",
    }


def acoustic_events(
    features: dict[str, Any], reference: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    if features["quality"] != "assessable":
        return []
    if reference is not None and reference["quality"] != "assessable":
        raise ValueError("reference audio has insufficient quality")
    threshold = features["config"]["long_pause_seconds"]
    if reference is not None:
        threshold = max(threshold, reference["longest_internal_pause_seconds"] + 1)
    return [
        {
            "event_type": "pause_change" if reference else "long_pause_observed",
            **pause,
            "reference_used": reference is not None,
        }
        for pause in features["internal_pauses"]
        if pause["duration_seconds"] >= threshold - 1e-8
    ]
