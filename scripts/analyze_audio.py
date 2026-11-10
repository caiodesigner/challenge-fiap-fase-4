"""CLI: processamento local por padrão; --azure habilita serviços configurados."""

import argparse
import json
from pathlib import Path

from monitoramento_clinico.audio import analyze_audio
from monitoramento_clinico.azure_audio import load_local_env
from monitoramento_clinico.local_speech import LocalSpeechClient

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("audio", type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--manual-transcript")
    parser.add_argument("--azure", action="store_true")
    parser.add_argument("--whisper", action="store_true")
    parser.add_argument(
        "--model", type=Path, default=Path("models/faster-whisper-small")
    )
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--output", type=Path, default=Path("outputs/audio"))
    args = parser.parse_args()
    load_local_env(Path(__file__).resolve().parents[1] / ".env")
    report = analyze_audio(
        args.audio,
        args.output,
        reference=args.reference,
        manual_transcript=args.manual_transcript,
        use_azure=args.azure,
        use_whisper=args.whisper,
        local_client=LocalSpeechClient(args.model, args.device)
        if args.whisper
        else None,
    )
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "acoustics"},
            indent=2,
        )
    )
