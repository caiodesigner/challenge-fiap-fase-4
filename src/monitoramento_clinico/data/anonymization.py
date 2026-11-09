"""Política mínima de detecção de identificadores em dados publicáveis."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    """Possível identificador encontrado em um texto."""

    kind: str
    value: str


PATTERNS: dict[str, re.Pattern[str]] = {
    "cpf": re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
    "email": re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"(?<!\d)(?:\+55\s*)?\(?\d{2}\)?\s*9?\d{4}[- ]?\d{4}(?!\d)"),
}

FORBIDDEN_KEYS = frozenset(
    {
        "cpf",
        "email",
        "telefone",
        "phone",
        "endereco",
        "address",
        "nome_completo",
        "full_name",
    }
)


def scan_text(text: str) -> list[Finding]:
    """Localiza padrões explícitos; não certifica anonimização de dados reais."""

    return [
        Finding(kind=kind, value=match.group(0))
        for kind, pattern in PATTERNS.items()
        for match in pattern.finditer(text)
    ]


def forbidden_keys(keys: Iterable[str]) -> set[str]:
    """Retorna nomes de campos que não podem compor o dataset publicável."""

    return {key for key in keys if key.casefold() in FORBIDDEN_KEYS}
