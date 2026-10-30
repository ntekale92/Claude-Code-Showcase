PY ?= python3
export PYTHONPATH := src
DATA_MODE ?= sample
export DATA_MODE

.PHONY: install sample build test quality evals check brief fetch clean

install:
	$(PY) -m pip install -r requirements.txt

sample:            ## regenerate synthetic sample files (real-file layout)
	$(PY) -m oda.samples

build:             ## build the warehouse for DATA_MODE and export marts to CSV
	$(PY) -m oda.pipeline

test:
	$(PY) -m pytest -q

quality: build
	$(PY) -m oda.quality

evals: build
	$(PY) evals/run_evals.py

check: test quality evals   ## everything CI runs

brief: build       ## market brief; uses Claude when ANTHROPIC_API_KEY is set
	$(PY) -m oda.insights

fetch:             ## download real data (run on your own machine)
	$(PY) -m oda.fetch --nsw-years 2024 2025 2026 --dft

clean:
	rm -rf data/warehouse_*.duckdb data/marts_* reports .pytest_cache
