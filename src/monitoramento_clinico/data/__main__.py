"""Comandos reproduzíveis: python -m monitoramento_clinico.data generate|validate."""

import argparse
import json
from pathlib import Path

from monitoramento_clinico.contracts import (
    Alert,
    EvaluationCase,
    Event,
    Manifest,
    Measurement,
    MediaAsset,
    Patient,
    PrescriptionVersion,
    Session,
)
from monitoramento_clinico.data.fixtures import generate_dataset, write_json
from monitoramento_clinico.data.validation import validate_dataset


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["generate", "validate", "schemas"])
    parser.add_argument("--root", type=Path, default=Path("data/fixtures"))
    args = parser.parse_args()
    if args.command == "schemas":
        for model in (
            Patient,
            Session,
            Measurement,
            PrescriptionVersion,
            MediaAsset,
            Event,
            Alert,
            EvaluationCase,
            Manifest,
        ):
            write_json(
                args.root / f"{model.__name__}.schema.json", model.model_json_schema()
            )
    else:
        if args.command == "generate":
            generate_dataset(args.root)
        print(json.dumps(validate_dataset(args.root), indent=2))


if __name__ == "__main__":
    main()
