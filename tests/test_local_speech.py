from pathlib import Path
from types import SimpleNamespace

import pytest
from test_audio import wav

from monitoramento_clinico.audio import analyze_audio
from monitoramento_clinico.local_speech import LocalSpeechClient


def test_local_backend_is_offline_and_preserves_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model_path = tmp_path / "model"
    model_path.mkdir()
    (model_path / "model.bin").write_bytes(b"test weights")

    class Model:
        def transcribe(self, path: str, **kwargs: object) -> tuple:
            assert kwargs["language"] == "pt"
            assert kwargs["vad_filter"] is True
            return iter(
                [
                    SimpleNamespace(
                        start=0, end=1, text="Estou com falta de ar.", words=[]
                    )
                ]
            ), SimpleNamespace(language="pt")

    monkeypatch.setattr(
        "monitoramento_clinico.local_speech.load_model", lambda *args: Model()
    )
    report = analyze_audio(
        wav(tmp_path / "source.wav"),
        tmp_path / "out",
        use_whisper=True,
        local_client=LocalSpeechClient(model_path),
    )
    assert report["status"] == "completed"
    assert report["transcript_source"] == "faster_whisper_local"
    assert report["cloud_request_count"] == 0
    assert report["real_azure_validation"] is False
    assert report["local_speech"]["network_used"] is False
    assert report["local_speech"]["manual_review_required"] is True
    assert report["local_speech"]["recognition_quality_validated"] is False
    assert report["events"][0]["event_type"] == "critical_mention"


def test_missing_model_preserves_acoustics(tmp_path: Path) -> None:
    report = analyze_audio(
        wav(tmp_path / "source.wav"),
        tmp_path / "out",
        use_whisper=True,
        local_client=LocalSpeechClient(tmp_path / "missing"),
    )
    assert report["status"] == "partial"
    assert report["local_speech"]["status"] == "failed"
    assert report["acoustics"]["quality"] == "assessable"


def test_silence_does_not_load_whisper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        LocalSpeechClient,
        "transcribe",
        lambda *args: pytest.fail("unexpected inference"),
    )
    report = analyze_audio(
        wav(tmp_path / "source.wav", silent=True), tmp_path / "out", use_whisper=True
    )
    assert report["local_speech"]["status"] == "skipped_quality"


def test_cuda_selection_without_gpu_is_explicit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "model.bin").write_bytes(b"test weights")
    monkeypatch.setattr("monitoramento_clinico.local_speech.local_gpu_count", lambda: 0)
    with pytest.raises(ValueError, match="not accessible"):
        LocalSpeechClient(tmp_path, device="cuda").transcribe(tmp_path / "unused.wav")


def test_transcription_sources_cannot_be_combined(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="one transcription"):
        analyze_audio(
            tmp_path / "unused", tmp_path / "out", use_whisper=True, use_azure=True
        )
