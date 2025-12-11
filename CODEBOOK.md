# Dataset Codebook

This codebook documents the curated outputs for the GLP-1 Safety Surveillance Dataset.

## Relations

- Reports.csv: One row per FAERS case (`safetyreportid`)
- Drugs.csv: One row per (case, product)
- Reactions.csv: One row per (case, reaction term)
- Safety_surveillance.csv: One row per case with list-aggregated drugs/reactions

## Reports.csv Fields

- safetyreportid: String; FAERS case identifier (primary key)
- received_date: Date (ISO-8601); date report was received (YYYY-MM-DD)
- event_date: Date (ISO-8601); date of adverse event when available
- patient_age_years: Float; patient age converted to years
- age_unit_raw: String; original age unit code (YR, MON, DY, etc.)
- patient_sex: String; standardized sex: F, M, or U (unknown)
- reporter_type: String; standardized: PHYSICIAN, PHARMACIST, CONSUMER, OTHER
- reporter_type_raw: String; original reporter qualification text
- country: String; ISO-3166 alpha-2 country code (uppercased)
- country_raw: String; original country value
- death: Boolean; outcome flag: death reported
- hospitalization: Boolean; outcome flag: hospitalization reported
- life_threatening: Boolean; outcome flag: life-threatening event
- disability: Boolean; outcome flag: disability reported
- congenital_anomaly: Boolean; outcome flag: congenital anomaly
- intervention: Boolean; outcome flag: required intervention
- other: Boolean; outcome flag: other serious outcome

## Drugs.csv Fields

- safetyreportid: String; foreign key to Reports.csv
- drug_role: String; PRIMARY, SECONDARY, or ASSOCIATED
- drug_name_original: String; original medicinal product name from FAERS
- rxcui: String; RxNorm Concept Unique Identifier (best-effort resolution)
- ingredient_rxcui: String; RxNorm ingredient-level RxCUI
- ingredient_name: String; normalized ingredient name from RxNorm
- brand_name: String; brand name (placeholder for future enrichment)

## Reactions.csv Fields

- safetyreportid: String; foreign key to Reports.csv
- reaction_term_text: String; MedDRA Preferred Term (whitespace normalized)

## Aggregated CSV

Safety_surveillance.csv joins Reports with list-aggregated Drugs and Reactions columns for convenience analysis.

## Provenance Files

- logs/run_<run_id>.json: Run metadata: query window, API parameters, drugs/brands
- logs/requests_<run_id>.jsonl: Per-request log: URL, params, status, record count, timing
- artifacts/raw_faers/manifest_<run_id>.json: Raw file manifest with SHA-256 checksum
- deliverables/MANIFEST.txt: Row counts and checksums for curated CSVs
- deliverables/QA_SUMMARY.md: Validation summary: totals, rejections, field completeness

## Data Quality Notes

- Deduplication: Records are deduplicated by `safetyreportid`, keeping the most complete record (highest non-null field count) with tie-break on latest `received_date`.
- Schema validation: Records missing `safetyreportid`, `patient` object, or both drugs and reactions are rejected and counted in QA_SUMMARY.md.
- RxNorm resolution: Name-based lookup; not all products resolve to RxCUI.
- FAERS limitations: Voluntary reporting system; cannot estimate incidence or risk. Subject to under-reporting, duplicate reports, and reporting bias.

## How to Run

1) Install dependencies
```bash
pip install -r requirements.txt
```

2) Acquire raw FAERS JSON (writes to artifacts/raw_faers)
```bash
python cli.py acquire --from 2021-01-01 --to 2025-12-31 --country US --drugs semaglutide,tirzepatide --brands Ozempic,Mounjaro --out artifacts/raw_faers
```

3) Process into deliverables/ (Reports.csv, Drugs.csv, Reactions.csv, Safety_surveillance.csv)
```bash
python cli.py process --raw-file artifacts/raw_faers/faers_<run_id>.json --out-dir deliverables
```

4) Create release archive
```bash
python scripts/release.py --deliverables-dir deliverables --out releases
```
