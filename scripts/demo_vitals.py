"""Demonstração reproduzível da primeira integração, sem sensores ou Azure."""

import argparse
import json
import platform
import tempfile
from pathlib import Path

from monitoramento_clinico.replay import load_case, replay
from monitoramento_clinico.vitals import VitalsConfig, VitalsMonitor

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--speed", type=float, default=1)
    parser.add_argument(
        "--report", type=Path, default=ROOT / "reports/vitals/demo.json"
    )
    args = parser.parse_args()
    config = VitalsConfig.model_validate_json(
        (ROOT / "configs/vitals.json").read_text()
    )
    cases = {}
    with tempfile.TemporaryDirectory(prefix="fiap-vitals-") as directory:
        for variant, expected in ((1, 0), (2, 4), (4, 0)):
            identifier = f"development-vitals-{variant}"
            monitor = VitalsMonitor(Path(directory) / f"{variant}.db", config)
            session, samples = load_case(ROOT / "data/fixtures", identifier)
            speed = args.speed if variant == 2 else 0
            summary = replay(monitor, session, samples, speed=speed)
            if summary["new_alerts"] != expected:
                raise AssertionError(f"unexpected detection count: {identifier}")
            if variant == 2:
                restored = VitalsMonitor(monitor.path, config)
                repeated = replay(restored, session, samples, speed=0)
                if repeated["new_alerts"] != 0 or repeated["statuses"] != {
                    "duplicate": 80
                }:
                    raise AssertionError("replay deduplication failed")
                alert_id = restored.snapshot()["alerts"][0]["alert_id"]
                restored.review_alert(
                    alert_id,
                    "acknowledge",
                    "demo-professional",
                    "Synthetic alert inspected",
                )
                restored.review_alert(
                    alert_id,
                    "close",
                    "demo-professional",
                    "Confirmed against synthetic fixture",
                    "confirmed",
                )
                cases[identifier] = {
                    "summary": summary,
                    "repeated": repeated,
                    "snapshot": VitalsMonitor(monitor.path, config).snapshot(),
                }
            else:
                cases[identifier] = {"summary": summary, "snapshot": monitor.snapshot()}
    report = {
        "purpose": "functional demonstration only",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "config": config.model_dump(),
        "config_fingerprint": config.fingerprint,
        "cases": cases,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({name: data["summary"] for name, data in cases.items()}, indent=2))


if __name__ == "__main__":
    main()
