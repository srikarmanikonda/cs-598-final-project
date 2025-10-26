# Dataset Codebook

This codebook documents the curated outputs.

Relations
- Reports.csv: one row per FAERS case (`safetyreportid`)
- Drugs.csv: one row per (case, product)
- Reactions.csv: one row per (case, reaction term)
- Safety_surveillance.csv: left-joined aggregation (lists per case) for convenience

Reports.csv Fields
- safetyreportid: String; FAERS case ID
- received_date: ISO-8601 date (YYYY-MM-DD) when available
- event_date: ISO-8601 date derived from `receiptdate` when present
- patient_age_years: Age in years (float), converted when unit available
- age_unit_raw: Original age unit code/string
- patient_sex: F/M/U standardized
- reporter_type: PHYSICIAN/PHARMACIST/CONSUMER/OTHER
- reporter_type_raw: Original reporter text (if present)
- country: ISO-3166 alpha-2 uppercased if provided
- country_raw: Original occurcountry
- death, hospitalization, life_threatening, disability, congenital_anomaly, intervention, other: boolean flags

Drugs.csv Fields
- safetyreportid: Join key
- drug_role: PRIMARY/SECONDARY/ASSOCIATED (mapped from FAERS characterization)
- drug_name_original: Original medicinal product string
- rxcui: RxNorm concept ID resolved by name (best effort)
- ingredient_rxcui, ingredient_name, brand_name: placeholders for future enrichment

Reactions.csv Fields
- safetyreportid: Join key
- reaction_term_text: MedDRA PT as provided (trimmed whitespace)

Aggregated CSV
- Safety_surveillance.csv: Reports joined with list-aggregated Drugs and Reactions by case

Provenance
- `logs/run_<run_id>.json`: window, query parameters
- `logs/requests_<run_id>.jsonl`: per-request log entries

Notes
- FAERS data may contain duplicates and variable completeness; deduplication keeps the most complete record per `safetyreportid` with a tie-break on latest `received_date`.
- RxNorm resolution is name-based and best-effort; not all products will resolve.





## How to Run

1) Install dependencies
```bash
make install
```

2) Acquire raw FAERS JSON (writes to artifacts/raw_faers)
```bash
python cli.py acquire --from 2021-01-01 --to 2025-12-31 --country US --drugs semaglutide,tirzepatide --brands Ozempic,Mounjaro --out artifacts/raw_faers
```

3) Process into deliverables/ (Reports.csv, Drugs.csv, Reactions.csv, Safety_surveillance.csv)
```bash
python cli.py process --raw-file artifacts/raw_faers/faers_<run_id>.json --out-dir deliverables
```

Alternative via Makefile
```bash
make acquire
make process
```
