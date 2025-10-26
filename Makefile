PYTHON ?= python3
PIP ?= pip3

.PHONY: install acquire process analyze release fmt

install:
	$(PIP) install -r requirements.txt

acquire:
	$(PYTHON) cli.py acquire --from 2021-01-01 --to 2025-12-31 --country US --drugs semaglutide,tirzepatide --brands Ozempic,Mounjaro --out artifacts/raw_faers

process:
	$(PYTHON) cli.py process --raw-file artifacts/raw_faers/$(shell ls -t artifacts/raw_faers/faers_*.json | head -1) --out-dir deliverables

analyze:
	jupyter notebook notebooks/analysis.ipynb

release:
	@echo "Consider zipping deliverables/ and including MANIFEST.txt (future step)"


