.PHONY: install check test data validate schemas demo-vitals ui video-model evaluate
PYTHON ?= python3
VENV_PYTHON := .venv/bin/python

install:
	$(PYTHON) -m venv .venv
	$(VENV_PYTHON) -m pip install -e '.[dev]'

test:
	$(VENV_PYTHON) -m pytest

check:
	$(VENV_PYTHON) -m ruff check .
	$(VENV_PYTHON) -m ruff format --check .
	$(VENV_PYTHON) -m mypy
	$(VENV_PYTHON) -m pytest
	$(VENV_PYTHON) -m monitoramento_clinico.data validate
	$(VENV_PYTHON) scripts/prepare_bidmc.py validate

data:
	$(VENV_PYTHON) -m monitoramento_clinico.data generate

validate:
	$(VENV_PYTHON) -m monitoramento_clinico.data validate
	$(VENV_PYTHON) scripts/prepare_bidmc.py validate

schemas:
	$(VENV_PYTHON) -m monitoramento_clinico.data schemas --root data/schemas

demo-vitals:
	$(VENV_PYTHON) scripts/demo_vitals.py

ui:
	$(VENV_PYTHON) -m streamlit run app.py

video-model:
	$(VENV_PYTHON) scripts/prepare_pose_model.py

evaluate:
	$(VENV_PYTHON) scripts/evaluate_local.py

.PHONY: install-full ready delivery
install-full:
	$(PYTHON) -m venv .venv
	$(VENV_PYTHON) -m pip install -e '.[audio,video,ui,dev]'

ready:
	$(VENV_PYTHON) scripts/check_delivery.py

delivery: check ready
	$(VENV_PYTHON) scripts/demo_clinical_fusion.py --database outputs/entrega/clinical-v2.db --report outputs/entrega/clinical-v2.json
	$(VENV_PYTHON) scripts/evaluate_local.py --fusion-report outputs/entrega/clinical-v2.json --output outputs/entrega/development-v2.json
	$(VENV_PYTHON) scripts/evaluate_local.py --split validation --output outputs/entrega/validation-v2.json
	$(VENV_PYTHON) scripts/evaluate_local.py --split test --output outputs/entrega/test-v2.json
