"""Vocabulário crítico em português com contexto local e limitações explícitas."""

import re
import unicodedata
from typing import Any


def plain(text: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFD", text.casefold())
        if unicodedata.category(char) != "Mn"
    )


def analyze_mentions(text: str) -> list[dict[str, Any]]:
    mentions: list[dict[str, Any]] = []
    pattern = re.compile(
        r"\bfalta de ar\b|\bdor no peito\b|\btontura\b|"
        r"\bcansa[cç]o\b|\bdificuldade (?:para|de) respirar\b",
        re.I,
    )
    # Spans remain in the original text, including accented characters.
    clauses = re.finditer(r"[^.!?;,\n]+", text)
    for clause in clauses:
        sections = []
        cursor = 0
        for separator in re.finditer(r"\bmas\b|\be com\b", clause.group(), re.I):
            sections.append((cursor, clause.group()[cursor : separator.start()]))
            cursor = separator.end()
        sections.append((cursor, clause.group()[cursor:]))
        for sub_start, value in sections:
            for match in pattern.finditer(value):
                prefix = plain(value[: match.start()])
                before = " ".join(prefix.split()[-6:])
                uncertain = bool(
                    re.search(r"\bnao nego\b|\btalvez\b|\bnao sei\b", before)
                )
                negated = bool(re.search(r"\bnao\b|\bsem\b|\bnego\b|\bnunca\b", before))
                historical = bool(
                    re.search(
                        r"\bontem\b|\btive\b|\btinha\b|\bantes\b|"
                        r"semana passada|no passado",
                        plain(value[: match.end()]),
                    )
                )
                other = bool(
                    re.search(r"minha mae|meu pai|minha esposa|meu marido", prefix)
                )
                start = clause.start() + sub_start + match.start()
                mentions.append(
                    {
                        "term": plain(match.group()),
                        "matched_text": match.group(),
                        "start_character": start,
                        "end_character": start + len(match.group()),
                        "assertion": "uncertain"
                        if uncertain
                        else "negated"
                        if negated
                        else "affirmed",
                        "temporality": "historical" if historical else "current",
                        "subject": "other" if other else "patient",
                    }
                )
    return mentions
