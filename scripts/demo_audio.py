"""Demonstração acústica sintética e configuração Azure ausente; sem rede."""

import argparse
import math
import struct
import wave
from pathlib import Path

from monitoramento_clinico.audio import analyze_audio
from monitoramento_clinico.azure_audio import AzureAudioClient, AzureSettings
from monitoramento_clinico.data.fixtures import write_json

ROOT = Path(__file__).resolve().parents[1]


def make_tone(path: Path, pause: float = 0, silent: bool = False) -> None:
    values = []
    for index in range(int((1 + pause) * 16000)):
        second = index / 16000
        value = (
            0
            if silent or 0.5 <= second < 0.5 + pause
            else int(6000 * math.sin(2 * math.pi * 220 * second))
        )
        values.append(struct.pack("<h", value))
    with wave.open(str(path), "wb") as stream:
        stream.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        stream.writeframes(b"".join(values))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/audio-demo")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for name, pause, silent in (
        ("continuous", 0, False),
        ("pause", 2.2, False),
        ("silence", 0, True),
    ):
        make_tone(args.output / f"{name}.wav", pause, silent)
    reports = {}
    for name in ("continuous", "pause", "silence"):
        reports[name] = analyze_audio(
            args.output / f"{name}.wav",
            args.output / "results",
            manual_transcript="Não estou com falta de ar.",
            reference=args.output / "continuous.wav" if name == "pause" else None,
        )
    reports["azure_not_configured"] = analyze_audio(
        args.output / "continuous.wav",
        args.output / "results",
        use_azure=True,
        client=AzureAudioClient(AzureSettings.from_env({})),
    )
    assert reports["pause"]["acoustic_deviations"][0]["event_type"] == "pause_change"
    assert reports["silence"]["events"] == []
    assert reports["azure_not_configured"]["cloud_request_count"] == 0
    write_json(
        ROOT / "reports/audio/local-demo.json",
        {
            "purpose": "Technical synthetic tones, not speech or clinical validation",
            "real_azure_executed": False,
            "reports": reports,
        },
    )
    print(
        {
            name: {
                "status": report["status"],
                "quality": report["acoustics"]["quality"],
                "events": len(report["events"]),
            }
            for name, report in reports.items()
        }
    )
