import json
from pathlib import Path

import pytest
from test_audio import wav

from monitoramento_clinico.audio import analyze_audio
from monitoramento_clinico.sentiment import analyze_sentiment


@pytest.mark.parametrize(
    "text,label",
    [
        ("Estou feliz e tranquilo com o atendimento.", "positive"),
        ("Estou muito preocupada e com medo.", "negative"),
        ("Estou tranquila, mas preocupada com o exame.", "mixed"),
        ("A consulta está marcada para amanhã.", "neutral"),
        ("Não estou bem.", "negative"),
        ("O atendimento não é bom.", "negative"),
        ("O atendimento nao e bom.", "negative"),
        ("O atendimento não é ruim.", "neutral"),
        ("Não estou mais tão feliz.", "negative"),
        ("Não estou triste.", "neutral"),
        ("Estou sem medo.", "neutral"),
        ("Não estou triste. Estou feliz.", "positive"),
        ("Não estou feliz, mas estou tranquilo.", "mixed"),
        ("Não só estou feliz, estou confiante.", "positive"),
        ("Não nego estar preocupado.", "negative"),
        ("Estou bem preocupada com o resultado.", "negative"),
        ("Estou com falta de ar e dor no peito.", "neutral"),
        ("O exame ocorreu normalmente.", "neutral"),
    ],
)
def test_expressed_affect_negation_and_symptom_separation(
    text: str, label: str
) -> None:
    result = analyze_sentiment(text)
    assert result["status"] == "completed"
    assert result["label"] == label
    assert -1 <= result["score"] <= 1
    for item in result["evidence"]:
        assert (
            text[item["start_character"] : item["end_character"]]
            == item["matched_text"]
        )
        assert (
            text[item["context_start_character"] : item["context_end_character"]]
            == item["context"]
        )


@pytest.mark.parametrize("text", [None, "", "   ", "...", "123"])
def test_absent_text_is_unavailable_instead_of_neutral(text: str | None) -> None:
    result = analyze_sentiment(text)
    assert result["status"] == "not_assessable"
    assert result["label"] is None
    assert result["score"] is None
    assert result["evidence"] == []


def test_pipeline_persists_sanitized_sentiment_without_risk_event(
    tmp_path: Path,
) -> None:
    text = "Contato teste@example.org. Estou muito preocupada com o exame."
    report = analyze_audio(
        wav(tmp_path / "input.wav"),
        tmp_path / "reports",
        manual_transcript=text,
    )
    assert report["local_sentiment"]["label"] == "negative"
    assert report["cloud_request_count"] == 0
    assert report["events"] == []
    report_path = next((tmp_path / "reports").glob("*/report.json"))
    saved = json.loads(report_path.read_text())
    assert saved["local_sentiment"] == report["local_sentiment"]
    assert "teste@example.org" not in report_path.read_text()
    assert "teste@example.org" not in report_path.with_suffix(".md").read_text()
    assert "Sentimento textual local" in report_path.with_suffix(".md").read_text()
    for item in saved["local_sentiment"]["evidence"]:
        assert (
            saved["transcript"][item["start_character"] : item["end_character"]]
            == item["matched_text"]
        )


def test_no_transcription_is_not_reported_as_neutral(tmp_path: Path) -> None:
    report = analyze_audio(wav(tmp_path / "input.wav"), tmp_path / "reports")
    assert report["status"] == "completed"
    assert report["local_sentiment"]["status"] == "not_assessable"
    assert report["local_sentiment"]["label"] is None


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Bem, eu estou com bastante falta de ar.", "neutral"),
        ("Bem... eu estou com falta de ar.", "neutral"),
        ("Bem eu estou com falta de ar.", "neutral"),
        ("Bem, eu estou preocupado.", "negative"),
        ("Bem, estou feliz.", "positive"),
        ("Estou bem.", "positive"),
        ("Não estou bem.", "negative"),
        ("Tudo bem, obrigado.", "positive"),
        ("Fui bem atendido.", "positive"),
        ("Bem atendido, estou satisfeito.", "positive"),
    ],
)
def test_opening_bem_is_not_confused_with_wellbeing(text: str, expected: str) -> None:
    result = analyze_sentiment(text)
    assert result["label"] == expected
    if text.startswith(("Bem, eu", "Bem...", "Bem eu")):
        assert not any(e["matched_text"] == "Bem" for e in result["evidence"])
