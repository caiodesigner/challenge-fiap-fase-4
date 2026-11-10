"""Confere reprodução 1× sobre registros existentes sem tocar nos bancos do painel."""

import json
import tempfile
from pathlib import Path

from monitoramento_clinico.replay import load_case, replay
from monitoramento_clinico.vitals import VitalsConfig, VitalsMonitor

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    config = VitalsConfig.model_validate_json(
        (ROOT / "configs/vitals.json").read_text()
    )
    session, samples = load_case(ROOT / "data/fixtures", "development-vitals-2")
    with tempfile.TemporaryDirectory() as directory:
        monitor = VitalsMonitor(Path(directory) / "monitor.db", config)
        replay(monitor, session, samples, 0, source_id="agent-verification-initial")
        summary = replay(
            monitor, session, samples, 1, source_id="agent-verification-repeat"
        )
        restored = VitalsMonitor(monitor.path, config).snapshot()
        assert summary["statuses"] == {"duplicate": 80}
        assert len(restored["runs"]) == 2
        report = {
            "purpose": "isolated replay history verification",
            "summary": summary,
            "runs": restored["runs"],
            "total_alerts": len(restored["alerts"]),
        }
    path = ROOT / "reports/vitals/replay-history.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
