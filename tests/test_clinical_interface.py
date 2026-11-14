import json
from pathlib import Path

import pytest

testing = pytest.importorskip("streamlit.testing.v1")
ROOT = Path(__file__).resolve().parents[1]


def test_clinical_panel_demo_persists_without_duplicate_alerts(tmp_path: Path) -> None:
    (tmp_path / "data").symlink_to(ROOT / "data", target_is_directory=True)
    (tmp_path / "configs").symlink_to(ROOT / "configs", target_is_directory=True)
    code = (
        "from pathlib import Path\n"
        "from monitoramento_clinico.clinical_ui import render_clinical_panel\n"
        f"render_clinical_panel(Path({str(tmp_path)!r}))"
    )
    panel = testing.AppTest.from_string(code, default_timeout=30).run()
    panel.selectbox[0].set_value(3).run()
    panel.button[0].click().run()
    assert not panel.exception
    payload = json.loads(panel.json[0].value)
    assert any(
        e["event_type"] == "unexpected_prescription_change" for e in payload["events"]
    )
    count = len(panel.get("download_button"))
    before = len(payload["events"])
    panel.button[0].click().run()
    assert not panel.exception
    assert len(json.loads(panel.json[0].value)["events"]) == before
    assert len(panel.get("download_button")) == count == 1
