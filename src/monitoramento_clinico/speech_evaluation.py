"""Avaliação independente: referências humanas nunca entram na inferência."""

import re
from collections import Counter
from typing import Any

from monitoramento_clinico.clinical_text import analyze_mentions, plain


def word_errors(reference: str, hypothesis: str) -> dict[str, Any]:
    expected = re.findall(r"\w+", plain(reference))
    actual = re.findall(r"\w+", plain(hypothesis))
    if not expected:
        raise ValueError("manual reference must contain words")
    previous = list(range(len(actual) + 1))
    for i, left in enumerate(expected, 1):
        current = [i]
        for j, right in enumerate(actual, 1):
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + (left != right),
                )
            )
        previous = current
    return {
        "word_errors": previous[-1],
        "reference_words": len(expected),
        "wer": previous[-1] / len(expected),
    }


def compare_transcripts(reference: str, hypothesis: str) -> dict[str, Any]:
    def mentions(text: str) -> Counter[tuple[str, ...]]:
        return Counter(
            (item["term"], item["assertion"], item["temporality"], item["subject"])
            for item in analyze_mentions(text)
        )

    expected, actual = mentions(reference), mentions(hypothesis)
    matched = sum((expected & actual).values())
    return {
        **word_errors(reference, hypothesis),
        "expected_mentions": sum(expected.values()),
        "matched_mentions_with_context": matched,
        "missed_mentions_with_context": sum((expected - actual).values()),
        "extra_mentions_with_context": sum((actual - expected).values()),
        "mention_context_exact_match": expected == actual,
    }
