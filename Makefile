# Omnipost Social Engine Makefile

.PHONY: help install install-dev test test-unit serve mcp mcp-config clean

PYTHON ?= python3

help:
	@echo "Omnipost Social Engine - Development Commands"
	@echo "============================================="
	@echo "  make install       Install omnipost package in editable mode"
	@echo "  make install-dev   Install omnipost with dev dependencies"
	@echo "  make test          Run full test suite with pytest"
	@echo "  make test-unit     Run tests using Python stdlib unittest"
	@echo "  make serve         Start Material 3 Studio web UI (http://localhost:8086)"
	@echo "  make mcp           Run stdio Model Context Protocol (MCP) server"
	@echo "  make mcp-config    Print MCP configuration snippets for AI clients"
	@echo "  make clean         Clean build and cache artifacts"

install:
	$(PYTHON) -m pip install -e .

install-dev:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	PYTHONPATH=src pytest tests -v

test-unit:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

serve:
	PYTHONPATH=src $(PYTHON) -m omnipost_social_engine serve --port 8086

mcp:
	PYTHONPATH=src $(PYTHON) -m omnipost_social_engine mcp

mcp-config:
	PYTHONPATH=src $(PYTHON) -m omnipost_social_engine mcp-config

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
