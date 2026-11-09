import sqlite3
from pathlib import Path

import pytest

from monitoramento_clinico.repositories.clinical import (
    ClinicalRepository,
    PatientNotFoundError,
)


@pytest.fixture
def repository(tmp_path: Path) -> ClinicalRepository:
    path = tmp_path / "clinical.db"
    schema = Path(__file__).resolve().parents[1] / "data/database/schema.sql"
    with sqlite3.connect(path) as connection:
        connection.executescript(schema.read_text())
        connection.executemany(
            "INSERT INTO patients VALUES (?, 1, 40, '2026-01-01')",
            [("PAT-SYN-001",), ("PAT-SYN-002",)],
        )
        connection.execute("INSERT INTO conditions VALUES ('PAT-SYN-001', 'HAS')")
        connection.execute("INSERT INTO allergies VALUES ('PAT-SYN-001', 'synthetic')")
        connection.execute("INSERT INTO medications VALUES ('PAT-SYN-001', 'MED-A', 1)")
        connection.execute(
            "INSERT INTO exams (patient_id, exam_code, status, requested_at) "
            "VALUES ('PAT-SYN-001', 'EX-A', 'pending', '2026-01-01')"
        )
        connection.execute(
            "INSERT INTO exams "
            "(patient_id, exam_code, status, requested_at, "
            "completed_at, result_summary) "
            "VALUES ('PAT-SYN-001', 'EX-B', 'completed', '2026-01-01', "
            "'2026-01-02', 'synthetic result')"
        )
    return ClinicalRepository(path)


def test_context_queries_and_patient_isolation(repository: ClinicalRepository) -> None:
    assert repository.patient_summary("PAT-SYN-001")["conditions"] == ["HAS"]
    assert repository.patient_summary("PAT-SYN-002")["conditions"] == []
    assert repository.active_medications("PAT-SYN-001") == ["MED-A"]
    assert repository.active_medications("PAT-SYN-002") == []
    assert repository.allergies("PAT-SYN-001") == ["synthetic"]
    assert repository.pending_exams("PAT-SYN-001")[0]["exam_code"] == "EX-A"
    assert repository.recent_results("PAT-SYN-001")[0]["exam_code"] == "EX-B"


@pytest.mark.parametrize("patient", ["PAT-SYN-999", "' OR 1=1 --"])
def test_invalid_or_missing_patient_is_rejected(
    repository: ClinicalRepository, patient: str
) -> None:
    with pytest.raises(PatientNotFoundError):
        repository.patient_summary(patient)


def test_database_is_read_only(repository: ClinicalRepository) -> None:
    with repository._connect() as connection:
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("DELETE FROM patients")


def test_query_limit_and_missing_database(
    repository: ClinicalRepository, tmp_path: Path
) -> None:
    with pytest.raises(ValueError):
        repository.recent_results("PAT-SYN-001", limit=0)
    with pytest.raises(FileNotFoundError):
        ClinicalRepository(tmp_path / "missing.db")
