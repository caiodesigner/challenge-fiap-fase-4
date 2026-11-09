import json
from pathlib import Path

import pytest

from monitoramento_clinico.data.fixtures import digest, generate_dataset, write_json
from monitoramento_clinico.data.validation import safe_path, validate_dataset


@pytest.fixture
def dataset(tmp_path: Path) -> Path:
    generate_dataset(tmp_path)
    return tmp_path


def test_deterministic_generation_and_distribution(
    dataset: Path, tmp_path: Path
) -> None:
    other = tmp_path / "second"
    generate_dataset(other)
    assert digest(dataset / "manifest.json") == digest(other / "manifest.json")
    summary = validate_dataset(dataset)
    assert summary["cases"] == 90
    assert summary["patients"] == 3
    assert summary["assets"] == 3
    assert set(summary["distribution"].values()) == {5}


def test_tampered_payload_is_rejected(dataset: Path) -> None:
    manifest = json.loads((dataset / "manifest.json").read_text())
    path = dataset / manifest["cases"][0]["path"]
    path.write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        validate_dataset(dataset)


def test_cross_split_patient_is_rejected(dataset: Path) -> None:
    path = dataset / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["cases"][0]["split"] = "test"
    write_json(path, manifest)
    with pytest.raises(ValueError, match="leakage"):
        validate_dataset(dataset)


def test_split_index_must_cover_exactly_its_cases(dataset: Path) -> None:
    write_json(dataset / "splits/test.json", [])
    with pytest.raises(ValueError, match="split index"):
        validate_dataset(dataset)


def test_payload_identity_must_match_manifest(dataset: Path) -> None:
    path = dataset / "manifest.json"
    manifest = json.loads(path.read_text())
    case = manifest["cases"][0]
    payload_path = dataset / case["path"]
    payload = json.loads(payload_path.read_text())
    payload["patient_id"] = "PAT-SYN-002"
    write_json(payload_path, payload)
    case["sha256"] = digest(payload_path)
    write_json(path, manifest)
    with pytest.raises(ValueError, match="identity"):
        validate_dataset(dataset)


def test_invalid_fixture_must_actually_fail_validation(dataset: Path) -> None:
    path = dataset / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["cases"][0]["input_status"] = "invalid"
    write_json(path, manifest)
    with pytest.raises(ValueError, match="was accepted"):
        validate_dataset(dataset)


def test_paths_cannot_escape_root(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="escapes"):
        safe_path(tmp_path, "../outside.json")


def test_committed_dataset_is_valid() -> None:
    root = Path(__file__).resolve().parents[1]
    assert validate_dataset(root / "data/fixtures")["cases"] == 90


def test_identifier_scanning_preserves_hashes_but_rejects_contact_fields() -> None:
    from monitoramento_clinico.data.validation import check_identifiers

    check_identifiers({"sha256": "a" * 20 + "12345678900" + "b" * 33})
    with pytest.raises(ValueError, match="identifier"):
        check_identifiers({"transcript": "Contato paciente@example.org"})
    with pytest.raises(ValueError, match="identifier"):
        check_identifiers({"sha256": "paciente@example.org"})
