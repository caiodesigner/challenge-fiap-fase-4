"""CLI do fluxo de sinais vitais e tratamento de alertas."""

import argparse
import json
from pathlib import Path
from typing import Literal

from monitoramento_clinico.replay import load_case, replay
from monitoramento_clinico.vitals import VitalsConfig, VitalsMonitor


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["replay", "status", "acknowledge", "close"])
    parser.add_argument("--database", type=Path, default=Path("outputs/monitoring.db"))
    parser.add_argument("--config", type=Path, default=Path("configs/vitals.json"))
    parser.add_argument("--fixtures", type=Path, default=Path("data/fixtures"))
    parser.add_argument("--case", default="development-vitals-2")
    parser.add_argument("--speed", type=float, default=1)
    parser.add_argument("--alert-id")
    parser.add_argument("--actor", default="demo-professional")
    parser.add_argument("--comment", default="Reviewed in synthetic demonstration")
    parser.add_argument(
        "--review", choices=["confirmed", "false_positive", "inconclusive"]
    )
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    config = VitalsConfig.model_validate_json(args.config.read_text())
    monitor = VitalsMonitor(args.database, config)
    if args.command == "replay":
        session, samples = load_case(args.fixtures, args.case)
        summary = replay(
            monitor,
            session,
            samples,
            args.speed,
            lambda sample, result: print(
                f"{sample.occurred_at.isoformat()} {sample.signal}: "
                f"{sample.value} {sample.unit} — {result.status} "
                f"alerts={len(result.alerts)}",
                flush=True,
            ),
        )
        payload = {"summary": summary, "snapshot": monitor.snapshot()}
    elif args.command in {"acknowledge", "close"}:
        if not args.alert_id:
            parser.error("--alert-id is required")
        action: Literal["acknowledge", "close"] = (
            "acknowledge" if args.command == "acknowledge" else "close"
        )
        monitor.review_alert(
            args.alert_id, action, args.actor, args.comment, args.review
        )
        payload = {"snapshot": monitor.snapshot()}
    else:
        payload = {"snapshot": monitor.snapshot()}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
