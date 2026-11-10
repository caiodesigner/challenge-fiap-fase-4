import io
import json
from pathlib import Path

import pytest
from test_audio import wav

from monitoramento_clinico.azure_audio import AzureSettings

testing = pytest.importorskip("streamlit.testing.v1")


def test_audio_panel_local_and_missing_azure_never_send_requests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Upload(io.BytesIO):
        name = "example.wav"

    source = wav(tmp_path / "source.wav", 2.2)

    def upload(label: str, **kwargs: object) -> Upload | None:
        return None if "Referência" in label else Upload(source.read_bytes())

    import streamlit

    monkeypatch.setattr(streamlit, "file_uploader", upload)
    missing = AzureSettings.from_env({})
    monkeypatch.setattr(
        AzureSettings, "from_env", classmethod(lambda cls, values=None: missing)
    )

    def forbidden(*args: object) -> None:
        raise AssertionError("unexpected HTTP request")

    monkeypatch.setattr("monitoramento_clinico.azure_audio.https_request", forbidden)
    code = (
        "from pathlib import Path\n"
        "from monitoramento_clinico.audio_ui import render_audio_panel\n"
        f"render_audio_panel(Path({str(tmp_path)!r}))"
    )
    panel = testing.AppTest.from_string(code, default_timeout=30).run()
    panel.radio[0].set_value("Somente local").run()
    panel.text_area[0].input("Não estou com falta de ar.")
    panel.button[0].click().run()
    assert not panel.exception
    assert len(panel.get("download_button")) == 2
    panel.run()
    assert not panel.exception
    panel.radio[0].set_value("Azure Speech + Language").run()
    panel.button[0].click().run()
    assert not panel.exception
    reports = [
        json.loads(path.read_text())
        for path in (tmp_path / "outputs/audio").glob("*/report.json")
    ]
    assert len(reports) == 2
    assert all(report["cloud_request_count"] == 0 for report in reports)
    assert {report["status"] for report in reports} == {"completed", "partial"}


def test_whisper_reference_evaluation_does_not_rerun_inference(tmp_path: Path) -> None:
    directory = tmp_path / "outputs/audio/example"
    directory.mkdir(parents=True)
    (directory / "report.json").write_text(
        json.dumps(
            {
                "transcript_source": "faster_whisper_local",
                "transcript": "Tenho falta de ar.",
                "cloud_requested": False,
            }
        )
    )
    (directory / "report.md").write_text("Test report")
    code = (
        "from pathlib import Path\n"
        "from monitoramento_clinico.audio_ui import render_audio_panel\n"
        f"render_audio_panel(Path({str(tmp_path)!r}))"
    )
    panel = testing.AppTest.from_string(code).run()
    panel.text_area[0].input("Não tenho falta de ar.").run()
    assert not panel.exception
    metrics = json.loads(panel.json[-1].value)
    assert metrics["matched_mentions_with_context"] == 0
    assert metrics["word_errors"] == 1
    assert json.loads((directory / "report.json").read_text())["transcript"] == (
        "Tenho falta de ar."
    )
