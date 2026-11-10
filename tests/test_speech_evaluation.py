import pytest

from monitoramento_clinico.speech_evaluation import compare_transcripts, word_errors


def test_original_failure_remains_visible() -> None:
    result = compare_transcripts(
        "Estou com falta de ar e sinto cansaço.",
        "Estou com falta de adicinho do cansaço.",
    )
    assert result["word_errors"] == 3
    assert result["wer"] == 0.375
    assert result["missed_mentions_with_context"] == 1


def test_negation_loss_is_not_counted_as_preserved_mention() -> None:
    result = compare_transcripts("Não tenho falta de ar.", "Tenho falta de ar.")
    assert result["matched_mentions_with_context"] == 0
    assert result["missed_mentions_with_context"] == 1
    assert result["extra_mentions_with_context"] == 1


def test_normalization_and_insertions() -> None:
    assert word_errors("Cansaço!", "cansaco")["wer"] == 0
    assert word_errors("dor", "dor no peito")["wer"] == 2
    with pytest.raises(ValueError, match="reference"):
        word_errors("...", "dor")


def test_subject_and_history_are_part_of_comparison() -> None:
    assert not compare_transcripts("Minha mãe teve falta de ar.", "Tenho falta de ar.")[
        "mention_context_exact_match"
    ]
