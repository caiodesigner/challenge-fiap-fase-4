"""Gera locução local por cena; requer Piper instalado separadamente."""

import argparse
import hashlib
import importlib
import json
import re
import subprocess
import wave
from pathlib import Path


def spoken_text(text: str) -> str:
    replacements = {
        "SPIRA": "Espira",
        "Whisper": "Uísper",
        "MediaPipe": "Mídia Páip",
        "SQLite": "ésse quiu láite",
        "CPU": "cê pê u",
        "JSON": "jêison",
        "REHAB24-6": "Rehab vinte e quatro, seis",
        "Sit-To-Stand": "sit tu sténd",
        "Arm VW": "Arm, vê, dáblio",
        "nove IADT": "nove, i, a, dê, tê",
        (
            "A locução será identificada como sintética "
            "caso esse recurso seja utilizado."
        ): "A locução é sintética.",
    }
    for original, replacement in replacements.items():
        text = text.replace(original, replacement)
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=Path("docs/roteiro-video.json"))
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/video-production/narration")
    )
    args = parser.parse_args()
    piper = importlib.import_module("piper")
    plan = json.loads(args.plan.read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    voice = piper.PiperVoice.load(str(args.model))
    config = piper.SynthesisConfig(length_scale=1.10, volume=0.85)
    rows = []
    chunks = []
    params = None
    for scene in plan["scenes"]:
        number = scene["scene"]
        slug = re.sub(r"[^a-z0-9]+", "-", scene["title"].lower()).strip("-")
        basename = f"{number:02}-{slug}"
        text = spoken_text(scene["narration"])
        target = args.output / f"{basename}.wav"
        (args.output / f"{basename}.txt").write_text(text + "\n")
        with wave.open(str(target), "wb") as wav:
            voice.synthesize_wav(text, wav, syn_config=config)
        with wave.open(str(target), "rb") as wav:
            params = wav.getparams()
            duration = wav.getnframes() / wav.getframerate()
            samples = wav.readframes(wav.getnframes())
        chunks.append((samples, scene["duration_seconds"]))
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(target),
                "-codec:a",
                "libmp3lame",
                "-q:a",
                "2",
                str(target.with_suffix(".mp3")),
            ],
            check=True,
        )
        row = {
            "scene": number,
            "title": scene["title"],
            "wav": str(target),
            "mp3": str(target.with_suffix(".mp3")),
            "duration_seconds": round(duration, 3),
            "scene_budget_seconds": scene["duration_seconds"],
            "spare_seconds": round(scene["duration_seconds"] - duration, 3),
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        }
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    assert params is not None
    for name, aligned in [
        ("locucao-continua.wav", False),
        ("locucao-sincronizada.wav", True),
    ]:
        with wave.open(str(args.output / name), "wb") as wav:
            wav.setparams(params)
            for samples, budget in chunks:
                wav.writeframes(samples)
                if aligned:
                    padding = int(
                        budget * params.framerate
                    ) * params.sampwidth * params.nchannels - len(samples)
                    if padding < 0:
                        raise ValueError(
                            "Narration exceeds scene budget; "
                            "adjust plan before alignment"
                        )
                    wav.writeframes(b"\0" * padding)
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(args.output / "locucao-continua.wav"),
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(args.output / "locucao-continua.mp3"),
        ],
        check=True,
    )
    manifest = {
        "engine": "piper-tts",
        "voice": args.model.name,
        "synthetic_voice": True,
        "model_sha256": hashlib.sha256(args.model.read_bytes()).hexdigest(),
        "plan_sha256": hashlib.sha256(args.plan.read_bytes()).hexdigest(),
        "inference": "local_cpu",
        "human_listening_review": "pending",
        "total_speech_seconds": round(sum(r["duration_seconds"] for r in rows), 3),
        "planned_video_seconds": plan["planned_duration_seconds"],
        "scenes": rows,
        "alignment_note": (
            "Silence padding at scene ends; not final audiovisual synchronization"
        ),
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
