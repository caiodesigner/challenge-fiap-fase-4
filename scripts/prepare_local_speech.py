"""Download explícito e versionado do Whisper multilíngue para uso offline."""

import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HOME", str(ROOT / "models/.hf-cache"))
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

if __name__ == "__main__":
    from huggingface_hub import HfApi, snapshot_download

    from monitoramento_clinico.data.fixtures import digest, write_json

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["base", "small", "medium"], default="small")
    parser.add_argument(
        "--revision", help="Optional upstream commit for exact reproduction"
    )
    args = parser.parse_args()
    repository = f"Systran/faster-whisper-{args.model}"
    revision = args.revision or HfApi().model_info(repository).sha
    if not revision:
        raise ValueError("model revision unavailable")
    path = ROOT / "models" / f"faster-whisper-{args.model}"
    snapshot_download(
        repository,
        revision=revision,
        local_dir=path,
        allow_patterns=[
            "config.json",
            "preprocessor_config.json",
            "model.bin",
            "tokenizer.json",
            "vocabulary.*",
        ],
    )
    write_json(
        path / "local-manifest.json",
        {
            "repository": repository,
            "revision": revision,
            "files": {
                file.name: digest(file)
                for file in path.iterdir()
                if file.is_file() and file.name != "local-manifest.json"
            },
            "purpose": "local speech transcription",
        },
    )
    print(f"Model ready offline: {path.name}; revision {revision}")
