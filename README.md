

## How to Run

```bash
# Clone repository
git clone https://github.com/srikarmanikonda/cs-598-final-project.git
cd cs-598-final-project


pip install -r requirements.txt

# Acquire raw FAERS data via CLI. NOTE: one will need an openFDA API key you can generate here: https://open.fda.gov/apis/authentication/

python cli.py acquire --from 2021-01-01 --to 2025-12-31 --country US \
    --drugs semaglutide,tirzepatide --brands Ozempic,Mounjaro \
    --out artifacts/raw_faers

# generate deliverables
python cli.py process --raw-file artifacts/raw_faers/faers_<run_id>.json \
    --out-dir deliverables

#  release
python scripts/release.py --deliverables-dir deliverables --out releases
```
