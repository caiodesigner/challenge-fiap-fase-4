"""Avaliação reproduzível de eventos locais; não executa modelos de mídia."""

import argparse
import importlib.metadata
import json
import platform
from datetime import UTC, datetime
from pathlib import Path

from monitoramento_clinico.data.fixtures import digest, write_json
from monitoramento_clinico.event_evaluation import alert_volume
from monitoramento_clinico.local_evaluation import evaluate_local_fixtures
from monitoramento_clinico.vitals import VitalsConfig

ROOT = Path(__file__).resolve().parents[1]


def markdown_report(report: dict) -> str:
    rows = [
        "# Avaliação funcional local",
        "",
        f"Partição: `{report['split']}`. Cadência: `{report['latency_scope']}`.",
        "Fixtures sintéticas; avaliação com mídias representativas permanece pendente.",
        "",
        "| Alternativa | TP | FP | FN | Precisão | Recall | F1 | p95 (ms) |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name, summary in report["summaries"].items():
        m = summary["metrics"]
        values = [
            name,
            m["true_positive"],
            m["false_positive"],
            m["false_negative"],
            m["precision"],
            m["recall"],
            m["f1"],
            summary["processing_p95_ms"],
        ]
        rows.append(
            "| "
            + " | ".join(
                "não definido"
                if v is None
                else f"{v:.4f}"
                if isinstance(v, float)
                else str(v)
                for v in values
            )
            + " |"
        )
    rows.extend(
        [
            "",
            "O JSON registra pareamentos, erros, referências e latência por caso.",
            "",
            "## Limites dos rótulos",
            "",
        ]
    )
    rows.extend(f"- {limitation}" for limitation in report["label_limitations"])
    if "fusion_volume" in report:
        volume = report["fusion_volume"]
        rows.extend(
            [
                "",
                "## Volume de alertas na fusão",
                "",
                f"{volume['events']} eventos: "
                f"{volume['isolated_alerts']} alertas isolados e "
                f"{volume['combined_alerts']} combinados.",
                "Sem referências multimodais, não há precisão/recall da fusão.",
            ]
        )
    return "\n".join(rows) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=ROOT / "data/fixtures")
    parser.add_argument("--config", type=Path, default=ROOT / "configs/vitals.json")
    parser.add_argument(
        "--protocol", type=Path, default=ROOT / "configs/evaluation.json"
    )
    parser.add_argument(
        "--split", choices=["development", "validation", "test"], default="development"
    )
    parser.add_argument("--speed", type=int, choices=[0, 1], default=0)
    parser.add_argument("--case", help="Optional single case from the selected split")
    parser.add_argument("--fusion-report", type=Path)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "outputs/evaluation/development.json"
    )
    args = parser.parse_args()
    report = evaluate_local_fixtures(
        args.fixtures,
        VitalsConfig.model_validate_json(args.config.read_text()),
        json.loads(args.protocol.read_text()),
        args.split,
        args.speed,
        args.case,
    )
    report.update(
        checked_at=datetime.now(UTC).isoformat(),
        protocol_sha256=digest(args.protocol),
        vitals_config_sha256=digest(args.config),
        environment={
            "python": platform.python_version(),
            "platform": platform.platform(),
            "pydantic": importlib.metadata.version("pydantic"),
        },
        cloud_requests=0,
        model_inference=False,
        implementation_sha256={
            name: digest(ROOT / "src/monitoramento_clinico" / name)
            for name in (
                "contracts.py",
                "vitals.py",
                "replay.py",
                "clinical_monitor.py",
                "event_evaluation.py",
                "local_evaluation.py",
            )
        },
    )
    if args.fusion_report:
        report["fusion_volume"] = {
            **alert_volume(json.loads(args.fusion_report.read_text())["snapshot"]),
            "source_sha256": digest(args.fusion_report),
        }
    write_json(args.output, report)
    args.output.with_suffix(".md").write_text(markdown_report(report))
    print(
        json.dumps(
            {"report": str(args.output), "summaries": report["summaries"]}, indent=2
        )
    )
