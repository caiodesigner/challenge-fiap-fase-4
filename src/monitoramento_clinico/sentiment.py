"""Baseline lexical de sentimentos em português, offline e com evidências."""

import re
from typing import Any

from monitoramento_clinico.clinical_text import plain

VERSION = "sentiment-pt-lexicon-v1"
LIMITATION = (
    "Baseline lexical em português; não interpreta ironia nem todo contexto, "
    "não estima confiança e não constitui avaliação clínica. "
    "Ausência de evidência polar é classificada como neutra."
)

# Lexicon of expressed affect; clinical symptoms alone are not sentiment cues.
POSITIVE = {
    "bem",
    "feliz",
    "felizes",
    "alegre",
    "alegres",
    "tranquilo",
    "tranquila",
    "tranquilos",
    "tranquilas",
    "calmo",
    "calma",
    "satisfeito",
    "satisfeita",
    "confortavel",
    "confortaveis",
    "otimo",
    "otima",
    "bom",
    "boa",
    "melhor",
    "melhorando",
    "aliviado",
    "aliviada",
    "confiante",
    "esperancoso",
    "esperancosa",
    "excelente",
    "acolhido",
    "acolhida",
}
NEGATIVE = {
    "mal",
    "triste",
    "tristes",
    "preocupado",
    "preocupada",
    "preocupados",
    "preocupadas",
    "medo",
    "receio",
    "ansioso",
    "ansiosa",
    "angustiado",
    "angustiada",
    "insatisfeito",
    "insatisfeita",
    "desconfortavel",
    "desconfortaveis",
    "pessimo",
    "pessima",
    "ruim",
    "pior",
    "piorando",
    "assustado",
    "assustada",
    "nervoso",
    "nervosa",
    "inseguro",
    "insegura",
    "frustrado",
    "frustrada",
    "desanimado",
    "desanimada",
    "horrivel",
}
NEGATORS = {"nao", "nunca", "nem", "sem", "nego"}
BOUNDARIES = {"mas", "porem", "contudo", "entretanto", "e"}


def analyze_sentiment(text: str | None) -> dict[str, Any]:
    """Classifica afeto no texto; negação de emoção negativa não implica positiva."""
    evidence: list[dict[str, Any]] = []
    result: dict[str, Any] = {
        "status": "not_assessable",
        "reason": "no_transcript",
        "label": None,
        "language": "pt",
        "method": "local_lexicon_rules",
        "version": VERSION,
        "score": None,
        "counts": {"positive": 0, "negative": 0, "neutral": 0},
        "evidence": evidence,
        "offsets": "sanitized_transcript_unicode_characters",
        "limitation": LIMITATION,
    }
    if not text or not re.search(r"[^\W\d_]", text, re.UNICODE):
        return result
    for clause in re.finditer(r"[^.!?;,\n]+", text):
        tokens = list(re.finditer(r"\w+", clause.group()))
        words = [plain(token.group()) for token in tokens]
        scope_start = 0
        for index, word in enumerate(words):
            is_conjunction = word != "e" or (
                tokens[index].group().casefold() == "e"
                and (index == 0 or words[index - 1] != "nao")
            )
            if word in BOUNDARIES and is_conjunction:
                scope_start = index + 1
                continue
            if word not in POSITIVE | NEGATIVE:
                continue
            # "bem preocupado" uses bem as an intensifier, not positive affect.
            if (
                word == "bem"
                and index + 1 < len(words)
                and words[index + 1] in NEGATIVE
            ):
                continue
            prefix_start = max(scope_start, index - 4)
            negators = []
            for position in range(prefix_start, index):
                if words[position] not in NEGATORS:
                    continue
                following = words[position + 1 : index]
                if words[position] == "nao" and (
                    following[:1] in (["so"], ["apenas"])
                    or following[:2] in (["e", "so"], ["e", "apenas"])
                ):
                    continue
                negators.append(position)
            negated = len(negators) % 2 == 1
            polarity = "positive" if word in POSITIVE else "negative"
            if negated:
                polarity = "negative" if polarity == "positive" else "neutral"
            start = clause.start() + tokens[index].start()
            end = clause.start() + tokens[index].end()
            context_start = clause.start() + tokens[prefix_start].start()
            evidence.append(
                {
                    "matched_text": text[start:end],
                    "start_character": start,
                    "end_character": end,
                    "context": text[context_start:end],
                    "context_start_character": context_start,
                    "context_end_character": end,
                    "negated": negated,
                    "polarity": polarity,
                }
            )
            result["counts"][polarity] += 1
    positive = result["counts"]["positive"]
    negative = result["counts"]["negative"]
    result.update(
        status="completed",
        reason="lexical_evidence" if evidence else "no_polar_evidence",
        label="mixed"
        if positive and negative
        else "positive"
        if positive
        else "negative"
        if negative
        else "neutral",
        score=(positive - negative) / (positive + negative)
        if positive + negative
        else 0.0,
    )
    return result
