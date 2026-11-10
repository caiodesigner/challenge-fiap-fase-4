"""Regressão do histórico e da revisão no painel, sem tocar nos bancos do usuário."""

from pathlib import Path

import pytest

from monitoramento_clinico.vitals import VitalsConfig, VitalsMonitor

testing = pytest.importorskip("streamlit.testing.v1")
ROOT = Path(__file__).resolve().parents[1]


def test_replays_and_review_remain_visible_after_rerun(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def isolated(path: Path, config: VitalsConfig) -> VitalsMonitor:
        return VitalsMonitor(tmp_path / path.name, config)

    monkeypatch.setattr("monitoramento_clinico.vitals.VitalsMonitor", isolated)
    panel = testing.AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    panel.selectbox[0].select("development-vitals-2").run()
    panel.checkbox[0].check().run()
    panel.button[0].click().run()
    panel.button[0].click().run()
    assert not panel.exception
    assert len(panel.selectbox[2].options) == 2
    panel.text_input[0].input("validation-professional")
    panel.text_input[1].input("Synthetic evidence reviewed")
    panel.button[1].click().run()
    panel.selectbox[4].select("Encerrar")
    panel.button[1].click().run()
    assert not panel.exception
    config = VitalsConfig.model_validate_json(
        (ROOT / "configs/vitals.json").read_text()
    )
    snapshot = VitalsMonitor(tmp_path / "development-vitals-2.db", config).snapshot()
    assert len(snapshot["runs"]) == 2
    assert snapshot["runs"][0]["summary"]["statuses"] == {"duplicate": 80}
    assert snapshot["alerts"][0]["status"] == "closed"
    assert len(snapshot["history"]) == 2
