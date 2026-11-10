.PHONY: install check test data validate schemas demo-vitals ui video-model
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
