.PHONY: install check test
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
