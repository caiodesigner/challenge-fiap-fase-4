from monitoramento_clinico.data.anonymization import forbidden_keys, scan_text


def test_detects_explicit_identifiers() -> None:
    findings = scan_text("Contato teste@example.org e CPF 123.456.789-00")
    assert {item.kind for item in findings} == {"cpf", "email"}


def test_rejects_forbidden_keys_case_insensitively() -> None:
    assert forbidden_keys(["patient_id", "Email", "nome_completo"]) == {
        "Email",
        "nome_completo",
    }


def test_allows_synthetic_identifiers() -> None:
    assert scan_text("PAT-SYN-001") == []
