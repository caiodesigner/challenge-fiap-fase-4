"""Consultas parametrizadas e minimizadas ao prontuário sintético."""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

PATIENT_ID = re.compile(r"^PAT-SYN-\d{3}$")


class PatientNotFoundError(LookupError):
    """Paciente sintético não encontrado ou identificador inválido."""


class ClinicalRepository:
    """Repositório somente leitura; não aceita fragmentos SQL externos."""

    def __init__(self, database_path: Path) -> None:
        if not database_path.is_file():
            raise FileNotFoundError(database_path)
        self.database_path = database_path.resolve()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        uri = f"file:{self.database_path.as_posix()}?mode=ro"
        connection = sqlite3.connect(uri, uri=True)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
        finally:
            connection.close()

    def _require_patient(self, connection: sqlite3.Connection, patient_id: str) -> None:
        if not PATIENT_ID.fullmatch(patient_id):
            raise PatientNotFoundError("identificador de paciente inválido")
        exists = connection.execute(
            "SELECT 1 FROM patients WHERE patient_id = ?", (patient_id,)
        ).fetchone()
        if exists is None:
            raise PatientNotFoundError(f"paciente não encontrado: {patient_id}")

    def patient_summary(self, patient_id: str) -> dict[str, Any]:
        """Retorna somente demografia mínima e listas pertinentes ao resumo."""

        with self._connect() as connection:
            self._require_patient(connection, patient_id)
            patient = connection.execute(
                """SELECT patient_id, age_years, last_review_date
                   FROM patients WHERE patient_id = ?""",
                (patient_id,),
            ).fetchone()
            assert patient is not None
            conditions = connection.execute(
                """SELECT condition_code FROM conditions
                   WHERE patient_id = ? ORDER BY condition_code""",
                (patient_id,),
            ).fetchall()
            return {
                "patient_id": patient["patient_id"],
                "age_years": patient["age_years"],
                "conditions": [row["condition_code"] for row in conditions],
                "last_review_date": patient["last_review_date"],
                "synthetic": True,
            }

    def pending_exams(self, patient_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            self._require_patient(connection, patient_id)
            rows = connection.execute(
                """SELECT exam_code, requested_at, status FROM exams
                   WHERE patient_id = ? AND status = 'pending'
                   ORDER BY requested_at, exam_code""",
                (patient_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def recent_results(
        self, patient_id: str, *, limit: int = 5
    ) -> list[dict[str, Any]]:
        if not 1 <= limit <= 20:
            raise ValueError("limit deve estar entre 1 e 20")
        with self._connect() as connection:
            self._require_patient(connection, patient_id)
            rows = connection.execute(
                """SELECT exam_code, completed_at, result_summary FROM exams
                   WHERE patient_id = ? AND status = 'completed'
                   ORDER BY completed_at DESC, exam_code LIMIT ?""",
                (patient_id, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def allergies(self, patient_id: str) -> list[str]:
        with self._connect() as connection:
            self._require_patient(connection, patient_id)
            rows = connection.execute(
                """SELECT substance FROM allergies
                   WHERE patient_id = ? ORDER BY substance""",
                (patient_id,),
            ).fetchall()
            return [str(row["substance"]) for row in rows]

    def active_medications(self, patient_id: str) -> list[str]:
        with self._connect() as connection:
            self._require_patient(connection, patient_id)
            rows = connection.execute(
                """SELECT medication_label FROM medications
                   WHERE patient_id = ? AND active = 1 ORDER BY medication_label""",
                (patient_id,),
            ).fetchall()
            return [str(row["medication_label"]) for row in rows]
