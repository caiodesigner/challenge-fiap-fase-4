import json
import math
import struct
import wave
from pathlib import Path

import pytest

from monitoramento_clinico.acoustics import acoustic_events, analyze_acoustics
from monitoramento_clinico.audio import analyze_audio
from monitoramento_clinico.azure_audio import (
    AzureAudioClient,
    AzureSettings,
    CloudError,
    azure_endpoint,
    load_local_env,
)
from monitoramento_clinico.clinical_text import analyze_mentions


def wav(path: Path, pause: float = 0, silent: bool = False) -> Path:
    samples = []
    for i in range(int((1 + pause) * 16000)):
        value = (
            0
            if silent or 0.5 <= i / 16000 < 0.5 + pause
            else int(6000 * math.sin(2 * math.pi * 220 * i / 16000))
        )
        samples.append(struct.pack("<h", value))
    with wave.open(str(path), "wb") as stream:
        stream.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        stream.writeframes(b"".join(samples))
    return path


def settings() -> AzureSettings:
    return AzureSettings.from_env(
        {
            "AZURE_SPEECH_KEY": "speech-test-secret",
            "AZURE_SPEECH_REGION": "eastus",
            "AZURE_LANGUAGE_KEY": "language-test-secret",
            "AZURE_LANGUAGE_ENDPOINT": "https://test.cognitiveservices.azure.com",
        }
    )


def test_energy_pauses_and_reference_comparison(tmp_path: Path) -> None:
    normal = analyze_acoustics(wav(tmp_path / "normal.wav"))
    altered = analyze_acoustics(wav(tmp_path / "pause.wav", 2.2))
    assert normal["quality"] == "assessable"
    assert normal["internal_pauses"] == []
    assert altered["longest_internal_pause_seconds"] == pytest.approx(2.2)
    assert acoustic_events(altered, normal)[0]["event_type"] == "pause_change"
    assert acoustic_events(altered, altered) == []


def test_silence_has_no_voice_event(tmp_path: Path) -> None:
    features = analyze_acoustics(wav(tmp_path / "silence.wav", silent=True))
    assert features["quality"] == "silence"
    assert acoustic_events(features) == []


def test_invalid_wav_generates_failed_report(tmp_path: Path) -> None:
    source = tmp_path / "bad.wav"
    source.write_bytes(b"invalid wav")
    with pytest.raises(ValueError):
        analyze_audio(source, tmp_path / "out")
    report = json.loads(next((tmp_path / "out").glob("*/report.json")).read_text())
    assert report["status"] == "failed"


@pytest.mark.parametrize(
    "text,assertion,temporality",
    [
        ("Estou com falta de ar.", "affirmed", "current"),
        ("Não estou com falta de ar.", "negated", "current"),
        ("Ontem tive falta de ar, agora estou bem.", "affirmed", "historical"),
        ("Talvez seja falta de ar.", "uncertain", "current"),
        ("Sem falta de ar.", "negated", "current"),
        ("Não nego falta de ar.", "uncertain", "current"),
    ],
)
def test_critical_term_context(text: str, assertion: str, temporality: str) -> None:
    mention = analyze_mentions(text)[0]
    assert mention["assertion"] == assertion
    assert mention["temporality"] == temporality
    assert (
        text[mention["start_character"] : mention["end_character"]]
        == mention["matched_text"]
    )


def test_negation_does_not_cross_clause_boundary() -> None:
    mentions = analyze_mentions("Não tenho falta de ar, mas estou com dor no peito.")
    assert [m["assertion"] for m in mentions] == ["negated", "affirmed"]


def test_local_pipeline_sanitizes_text_and_does_not_call_cloud(tmp_path: Path) -> None:
    def forbidden(*args: object) -> dict[str, object]:
        raise AssertionError("network should not be called")

    client = AzureAudioClient(settings(), transport=forbidden)
    report = analyze_audio(
        wav(tmp_path / "audio.wav"),
        tmp_path / "out",
        client=client,
        manual_transcript="Estou com falta de ar. Contato teste@example.org",
    )
    assert client.calls == 0
    assert report["real_azure_validation"] is False
    assert "teste@example.org" not in json.dumps(report)
    assert report["transcript_source"] == "manual_not_azure"
    assert report["events"][0]["event_type"] == "critical_mention"


def test_missing_configuration_preserves_local_analysis(tmp_path: Path) -> None:
    client = AzureAudioClient(AzureSettings.from_env({}))
    report = analyze_audio(
        wav(tmp_path / "audio.wav"), tmp_path / "out", use_azure=True, client=client
    )
    assert report["status"] == "partial"
    assert report["cloud"]["speech"]["status"] == "not_configured"
    assert report["cloud_request_count"] == 0
    assert report["acoustics"]["quality"] == "assessable"


def test_azure_protocol_with_test_transport_not_real_evidence(tmp_path: Path) -> None:
    requests = []

    def transport(
        url: str, body: bytes, headers: dict[str, str], timeout: float
    ) -> dict:
        requests.append((url, body, headers, timeout))
        if "speech/recognition" in url:
            assert "language=pt-BR" in url
            assert body[:4] == b"RIFF"
            return {
                "RecognitionStatus": "Success",
                "NBest": [{"Display": "Estou com falta de ar.", "Confidence": 0.9}],
            }
        payload = json.loads(body)
        assert payload["analysisInput"]["documents"][0]["language"] == "pt"
        doc = {
            "id": "1",
            "sentiment": "negative",
            "confidenceScores": {"negative": 0.9},
            "keyPhrases": ["falta de ar"],
        }
        return {
            "results": {
                "documents": [doc],
                "errors": [],
                "modelVersion": "test-version",
            }
        }

    client = AzureAudioClient(settings(), transport)
    report = analyze_audio(
        wav(tmp_path / "audio.wav"), tmp_path / "out", use_azure=True, client=client
    )
    assert len(requests) == 3
    assert all(result["status"] == "completed" for result in report["cloud"].values())
    assert report["real_azure_validation"] is False
    assert report["cloud_transport"] == "test_transport"
    assert "test-secret" not in json.dumps(report)
    assert report["cloud_request_count"] == 3


def test_cloud_failure_does_not_discard_acoustic_evidence(tmp_path: Path) -> None:
    def timeout(*args: object) -> dict:
        raise CloudError("Azure connection failed or timed out")

    report = analyze_audio(
        wav(tmp_path / "audio.wav", 2.2),
        tmp_path / "out",
        use_azure=True,
        client=AzureAudioClient(settings(), timeout),
    )
    assert report["status"] == "partial"
    assert report["cloud"]["speech"]["status"] == "failed"
    assert report["cloud_request_count"] == 1
    assert report["events"][0]["event_type"] == "long_pause_observed"


def test_silent_audio_skips_cloud(tmp_path: Path) -> None:
    client = AzureAudioClient(
        settings(), lambda *args: pytest.fail("unexpected request")
    )
    report = analyze_audio(
        wav(tmp_path / "silence.wav", silent=True),
        tmp_path / "out",
        use_azure=True,
        client=client,
    )
    assert report["cloud_request_count"] == 0
    assert report["cloud"]["speech"]["status"] == "skipped_quality"


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://test.cognitiveservices.azure.com",
        "https://attacker.example",
        "https://test.cognitiveservices.azure.com?key=secret",
    ],
)
def test_endpoint_does_not_send_credentials_to_arbitrary_hosts(endpoint: str) -> None:
    with pytest.raises(ValueError):
        azure_endpoint(endpoint)


def test_env_loader_never_executes_commands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("AZURE_SPEECH_KEY", raising=False)
    path = tmp_path / ".env"
    path.write_text("AZURE_SPEECH_KEY='$(touch should-not-exist)'\n")
    load_local_env(path)
    import os

    assert os.environ["AZURE_SPEECH_KEY"] == "$(touch should-not-exist)"
    assert not (tmp_path / "should-not-exist").exists()
