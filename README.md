# GLP-1 Safety Surveillance Dataset

NOTE: I've already run the workflow end to end. Please follow these instructions to re-run if needed but the full outputs will be present


A reproducible data curation pipeline for FDA Adverse Event Reporting System (FAERS) data on GLP-1 receptor agonists (semaglutide/Ozempic, tirzepatide/Mounjaro).

## Prerequisites

- Python 3.10+
- openFDA API key (optional but **strongly recommended** for faster data acquisition)

## Quick Start

### 1. Clone and Install Dependencies

```bash
git clone https://github.com/srikarmanikonda/cs-598-final-project.git
cd cs-598-final-project
pip install -r requirements.txt
```

### 2. Set Up API Key (Recommended)

Get a free openFDA API key at: https://open.fda.gov/apis/authentication/

Then set it as an environment variable:

```bash
export OPENFDA_API_KEY="your-api-key-here"
```

**Why?** Without an API key, openFDA limits you to 60 requests/minute. With a key, you get 240 requests/minute (4x faster).

### 3. Acquire Raw FAERS Data
Note: This Process takes a very long time

```bash
python cli.py acquire --from 2024-01-01 --to 2024-12-31 --country US \
    --drugs semaglutide,tirzepatide --brands Ozempic,Mounjaro \
    --out artifacts/raw_faers
```



**Note:** The `run_id` (e.g., `20251210T181512_ef230a80`) is generated automatically. You'll need it for the next step.

### 4. Process Into Curated Tables

```bash
python cli.py process --raw-file artifacts/raw_faers/faers_<run_id>.json --out-dir deliverables
```

Replace `<run_id>` with your actual run ID from step 3.

### 5. Create Release Archive

```bash
python scripts/release.py --deliverables-dir deliverables --out releases
```

**Expected output:**
```
Created release archive: releases/release_2025-12-10.zip
SHA-256: <checksum>
Checksum file: releases/release_2025-12-10.zip.sha256
```

### 6. Run Analysis Notebook (Optional)

```bash
jupyter notebook notebooks/analysis.ipynb
```

Or open `notebooks/analysis.ipynb` in VS Code/Cursor and run the cells.

## Output Files

After running the pipeline, you'll have:

| File | Description |
|------|-------------|
| `deliverables/Reports.csv` | One row per adverse event report (25K+ rows) |
| `deliverables/Drugs.csv` | One row per drug-report pair (136K+ rows) |
| `deliverables/Reactions.csv` | One row per reaction-report pair (65K+ rows) |
| `deliverables/Safety_surveillance.csv` | Aggregated view with list columns |
| `deliverables/MANIFEST.txt` | Row counts and SHA-256 checksums |
| `deliverables/QA_SUMMARY.md` | Validation statistics and field completeness |
| `deliverables/CODEBOOK.md` | Data dictionary |
| `deliverables/DATACITE.json` | DataCite metadata |
| `releases/release_<date>.zip` | Zipped deliverables with checksum |

## Project Structure

```
cs-598-final-project/
├── cli.py                 # Main command-line interface
├── src/
│   ├── acquire/           # FAERS data acquisition
│   ├── normalize/         # RxNorm drug normalization
│   ├── process/           # Data curation and validation
│   └── common/            # Shared utilities and config
├── scripts/
│   └── release.py         # Release archive creation
├── notebooks/
│   └── analysis.ipynb     # Exploratory analysis
├── artifacts/             # Raw data and caches
├── deliverables/          # Curated outputs
├── releases/              # Release archives
├── logs/                  # Provenance logs
├── CODEBOOK.md            # Data documentation
├── DATACITE.json          # Dataset metadata
└── REPORT.md              # Project report
```

## Troubleshooting

**"ModuleNotFoundError: No module named 'src'"**
- Make sure you're running commands from the project root dir