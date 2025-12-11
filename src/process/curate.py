import json
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from tqdm import tqdm

from src.common.config import PATHS, ensure_directories
from src.common.utils import parse_faers_date, sha256_file
from src.normalize.rxnorm_client import RxNormClient


def _safe_get(d: Dict[str, Any], path: List[str]) -> Any:
    cur: Any = d
    for key in path:
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return None
    return cur


def _standardize_gender(sex: Optional[str]) -> str:
    if not sex:
        return "U"
    s = str(sex).strip().upper()
    if s in ("F", "FEMALE"):
        return "F"
    if s in ("M", "MALE"):
        return "M"
    return "U"


def _standardize_reporter(rep: Optional[str]) -> Tuple[str, str]:
    if not rep:
        return ("OTHER", "")
    raw = str(rep)
    s = raw.strip().upper()
    if "PHYSICIAN" in s:
        return ("PHYSICIAN", raw)
    if "PHARMACIST" in s:
        return ("PHARMACIST", raw)
    if "CONSUMER" in s or "LAWYER" in s:
        return ("CONSUMER", raw)
    return ("OTHER", raw)


def _standardize_country(country: Optional[str]) -> Tuple[str, str]:
    if not country:
        return ("", "")
    raw = str(country)
    return (raw.strip().upper(), raw)


def _age_to_years(age_val: Optional[str], age_unit: Optional[str]) -> Tuple[Optional[float], str]:
    if age_val is None:
        return (None, age_unit or "")
    try:
        val = float(age_val)
    except Exception:
        return (None, age_unit or "")
    unit = (age_unit or "").strip().upper()
    if unit in ("YR", "YEAR", "YEARS"):
        return (val, unit)
    if unit in ("MON", "MONTH", "MONTHS"):
        return (val / 12.0, unit)
    if unit in ("WK", "WEEK", "WEEKS"):
        return (val / 52.0, unit)
    if unit in ("DY", "DAY", "DAYS"):
        return (val / 365.0, unit)
    if unit in ("HR", "HOUR", "HOURS"):
        return (val / (365.0 * 24.0), unit)
    return (val, unit)


def curate_tables(raw_json_path: str, out_dir: str) -> Dict[str, str]:
    ensure_directories()
    os.makedirs(out_dir, exist_ok=True)
    rx = RxNormClient()

    reports_rows: List[Dict[str, Any]] = []
    drugs_rows: List[Dict[str, Any]] = []
    reactions_rows: List[Dict[str, Any]] = []

    best_record: Dict[str, Dict[str, Any]] = {}
    completeness: Dict[str, int] = {}

    print("Loading raw JSON file...")
    with open(raw_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} records")

    if not isinstance(data, list):
        data = []

    def validate_record(rec: Any) -> Tuple[bool, str]:
        if not isinstance(rec, dict):
            return (False, "not_a_object")
        rep_id = rec.get("safetyreportid")
        if rep_id is None or str(rep_id).strip() == "":
            return (False, "missing_safetyreportid")
        patient = rec.get("patient")
        if not isinstance(patient, dict):
            return (False, "invalid_patient")
        drugs_list = patient.get("drug")
        reactions_list = patient.get("reaction")
        if (not isinstance(drugs_list, list) or len(drugs_list) == 0) and (
            not isinstance(reactions_list, list) or len(reactions_list) == 0
        ):
            return (False, "no_drug_no_reaction")
        return (True, "")

    rejected_reasons: Dict[str, int] = defaultdict(int)
    valid_records: List[Dict[str, Any]] = []
    print("Validating records...")
    for rec in tqdm(data, desc="Validating"):
        ok, reason = validate_record(rec)
        if ok:
            valid_records.append(rec)
        else:
            rejected_reasons[reason] += 1

    total_input = len(data)
    total_valid = len(valid_records)
    total_rejected = total_input - total_valid

    print("Deduplicating records...")
    for rec in valid_records:
        rep_id = rec.get("safetyreportid")
        if not rep_id:
            continue
        non_missing = sum(1 for k, v in rec.items() if v not in (None, "", [], {}))
        prev = completeness.get(rep_id, -1)
        if non_missing > prev:
            best_record[rep_id] = rec
            completeness[rep_id] = non_missing
        elif non_missing == prev:
            prev_date = parse_faers_date(best_record[rep_id].get("receivedate"))
            cur_date = parse_faers_date(rec.get("receivedate"))
            if (cur_date or "") > (prev_date or ""):
                best_record[rep_id] = rec
                completeness[rep_id] = non_missing
    print(f"Deduplicated to {len(best_record)} unique reports")

    print(f"Processing {len(best_record)} reports (with RxNorm lookups)...")
    for rep_id, rec in tqdm(best_record.items(), desc="Processing"):
        received_date = parse_faers_date(rec.get("receivedate"))
        event_date = parse_faers_date(rec.get("receiptdate"))

        patient = rec.get("patient", {})
        sex = _standardize_gender(patient.get("sex") if isinstance(patient.get("sex"), str) else str(patient.get("sex")))
        age_val = None
        age_unit = None
        if isinstance(patient.get("patientonsetage"), (str, int, float)):
            age_val = str(patient.get("patientonsetage"))
        if isinstance(patient.get("patientonsetageunit"), (str, int, float)):
            age_unit = str(patient.get("patientonsetageunit"))
        age_years, age_unit_raw = _age_to_years(age_val, age_unit)

        occupation = patient.get("patientreporter") or rec.get("fulfillexpeditecriteria")
        reporter_type, reporter_type_raw = _standardize_reporter(str(occupation) if occupation is not None else None)
        country, country_raw = _standardize_country(rec.get("occurcountry"))

        death = bool(rec.get("seriousnessdeath"))
        hospitalization = bool(rec.get("seriousnesshospitalization"))
        life_threatening = bool(rec.get("seriousnesslifethreatening"))
        disability = bool(rec.get("seriousnessdisabling"))
        congenital_anomaly = bool(rec.get("seriousnesscongenitalanomali"))
        intervention = bool(rec.get("seriousnessother"))
        other = bool(rec.get("seriousnessother"))

        reports_rows.append(
            {
                "safetyreportid": rep_id,
                "received_date": received_date,
                "event_date": event_date,
                "patient_age_years": age_years,
                "age_unit_raw": age_unit_raw,
                "patient_sex": sex,
                "reporter_type": reporter_type,
                "reporter_type_raw": reporter_type_raw,
                "country": country,
                "country_raw": country_raw,
                "death": death,
                "hospitalization": hospitalization,
                "life_threatening": life_threatening,
                "disability": disability,
                "congenital_anomaly": congenital_anomaly,
                "intervention": intervention,
                "other": other,
            }
        )

        for d in (patient.get("drug") or []):
            if not isinstance(d, dict):
                continue
            original = d.get("medicinalproduct") or ""
            role = (d.get("drugcharacterization") or "").strip().upper()
            if role in ("1", "PRIMARY"):
                role_std = "PRIMARY"
            elif role in ("2", "SECONDARY"):
                role_std = "SECONDARY"
            else:
                role_std = "ASSOCIATED"


            target_drugs = ["semaglutide", "tirzepatide", "ozempic", "mounjaro", "wegovy", "rybelsus", "zepbound"]
            if original and any(t in original.lower() for t in target_drugs):
                rxcui = rx.get_rxcui(original)
                ing_rxcui, ing_name = rx.get_ingredient(rxcui) if rxcui else (None, None)
            else:
                rxcui, ing_rxcui, ing_name = None, None, None
            drugs_rows.append(
                {
                    "safetyreportid": rep_id,
                    "drug_role": role_std,
                    "drug_name_original": original,
                    "rxcui": rxcui,
                    "ingredient_rxcui": ing_rxcui,
                    "ingredient_name": ing_name,
                    "brand_name": None,
                }
            )

        for r in (patient.get("reaction") or []):
            if not isinstance(r, dict):
                continue
            term = r.get("reactionmeddrapt")
            if isinstance(term, str):
                reactions_rows.append({"safetyreportid": rep_id, "reaction_term_text": " ".join(term.split())})

    df_reports = pd.DataFrame(reports_rows)
    df_drugs = pd.DataFrame(drugs_rows)
    df_reactions = pd.DataFrame(reactions_rows)

    reports_csv = os.path.join(out_dir, "Reports.csv")
    drugs_csv = os.path.join(out_dir, "Drugs.csv")
    reactions_csv = os.path.join(out_dir, "Reactions.csv")
    df_reports.to_csv(reports_csv, index=False)
    df_drugs.to_csv(drugs_csv, index=False)
    df_reactions.to_csv(reactions_csv, index=False)

    agg = (
        df_reports.merge(df_drugs.groupby("safetyreportid").agg(list).reset_index(), on="safetyreportid", how="left")
        .merge(df_reactions.groupby("safetyreportid").agg(list).reset_index(), on="safetyreportid", how="left")
    )
    agg_csv = os.path.join(out_dir, "Safety_surveillance.csv")
    agg.to_csv(agg_csv, index=False)

    def pct_non_null(series: pd.Series) -> float:
        if len(series) == 0:
            return 0.0
        return float(series.notna().mean() * 100.0)

    completeness_rows = [
        ("received_date", pct_non_null(df_reports.get("received_date"))),
        ("patient_sex", pct_non_null(df_reports.get("patient_sex"))),
        ("patient_age_years", pct_non_null(df_reports.get("patient_age_years"))),
        ("country", pct_non_null(df_reports.get("country"))),
    ]

    qa_lines = []
    qa_lines.append(f"Raw file: {raw_json_path}")
    qa_lines.append(f"Total input records: {total_input}")
    qa_lines.append(f"Valid records (pre-dedup): {total_valid}")
    qa_lines.append(f"Rejected records: {total_rejected}")
    qa_lines.append("Rejection reasons:")
    if rejected_reasons:
        for reason, count in sorted(rejected_reasons.items()):
            qa_lines.append(f"- {reason}: {count}")
    else:
        qa_lines.append("- none")
    qa_lines.append("")
    qa_lines.append("Field completeness (Reports.csv):")
    for name, pct in completeness_rows:
        qa_lines.append(f"- {name}: {pct:.1f}% non-null")

    qa_path = os.path.join(out_dir, "QA_SUMMARY.md")
    with open(qa_path, "w", encoding="utf-8") as qf:
        qf.write("\n".join(qa_lines) + "\n")


    manifest_lines = []
    manifest_lines.append("MANIFEST")
    manifest_lines.append("========")
    manifest_lines.append("")
    manifest_lines.append("Row counts:")
    manifest_lines.append(f"- Reports.csv: {len(df_reports)} rows")
    manifest_lines.append(f"- Drugs.csv: {len(df_drugs)} rows")
    manifest_lines.append(f"- Reactions.csv: {len(df_reactions)} rows")
    manifest_lines.append(f"- Safety_surveillance.csv: {len(agg)} rows")
    manifest_lines.append("")
    manifest_lines.append("SHA-256 checksums:")
    manifest_lines.append(f"- Reports.csv: {sha256_file(reports_csv)}")
    manifest_lines.append(f"- Drugs.csv: {sha256_file(drugs_csv)}")
    manifest_lines.append(f"- Reactions.csv: {sha256_file(reactions_csv)}")
    manifest_lines.append(f"- Safety_surveillance.csv: {sha256_file(agg_csv)}")

    manifest_path = os.path.join(out_dir, "MANIFEST.txt")
    with open(manifest_path, "w", encoding="utf-8") as mf:
        mf.write("\n".join(manifest_lines) + "\n")

    return {
        "reports": reports_csv,
        "drugs": drugs_csv,
        "reactions": reactions_csv,
        "aggregated": agg_csv,
        "qa_summary": qa_path,
        "manifest": manifest_path,
    }
