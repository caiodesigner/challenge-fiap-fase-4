"""Compare modelos offline contra um manifesto de WAVs e referências manuais."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from monitoramento_clinico.data.fixtures import digest, write_json
from monitoramento_clinico.local_speech import LocalSpeechClient
from monitoramento_clinico.speech_evaluation import compare_transcripts

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--models", nargs="+", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/speech-evaluation.json")
    )
    args = parser.parse_args()
    samples = json.loads(args.manifest.read_text())["samples"]
    if not samples:
        raise ValueError("provide recordings and manual references before evaluation")
    results = []
    for model in args.models:
        client = LocalSpeechClient(model)
        for sample in samples:
            reference = sample["reference"]
            if not reference.strip() or sample["kind"] not in {"synthetic", "natural"}:
                raise ValueError("each sample needs a reference and kind")
            audio = (args.manifest.resolve().parent / sample["audio"]).resolve()
            # No prompt, vocabulary or expected text is passed to the recognizer.
            result = client.transcribe(audio)
            results.append(
                {
                    "sample_id": sample["id"],
                    "kind": sample["kind"],
                    "audio_sha256": digest(audio),
                    "model": model.name,
                    "reference": reference,
                    "hypothesis": result.pop("text"),
                    "inference": {k: v for k, v in result.items() if k != "segments"},
                }
            )
            results[-1]["metrics"] = compare_transcripts(
                reference, results[-1]["hypothesis"]
            )
            print(model.name, sample["id"], results[-1]["metrics"], flush=True)
    summaries = []
    for model in args.models:
        for kind in ("synthetic", "natural"):
            rows = [
                r for r in results if r["model"] == model.name and r["kind"] == kind
            ]
            if not rows:
                continue
            errors = sum(r["metrics"]["word_errors"] for r in rows)
            words = sum(r["metrics"]["reference_words"] for r in rows)
            summaries.append(
                {
                    "model": model.name,
                    "kind": kind,
                    "samples": len(rows),
                    "word_errors": errors,
                    "reference_words": words,
                    "weighted_wer": errors / words,
                    "missed_mentions_with_context": sum(
                        r["metrics"]["missed_mentions_with_context"] for r in rows
                    ),
                    "extra_mentions_with_context": sum(
                        r["metrics"]["extra_mentions_with_context"] for r in rows
                    ),
                }
            )
    write_json(
        args.output,
        {
            "checked_at": datetime.now(UTC).isoformat(),
            "manifest_sha256": digest(args.manifest),
            "results": results,
            "summaries": summaries,
            "natural_speech_evaluated": any(s["kind"] == "natural" for s in samples),
            "clinical_validation": False,
        },
    )
