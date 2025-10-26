import json
import os
import time
from typing import Dict, Iterable, List, Optional

import requests
from tqdm import tqdm

from src.common.config import OPENFDA, PATHS, ensure_directories
from src.common.logging_utils import RequestLog, append_request_log
from src.common.utils import sha256_file, write_json


def _build_search_query(
    drugs: List[str],
    brands: List[str],
    start_date: str,
    end_date: str,
    country: str,
) -> str:
    drug_terms = [f'patient.drug.medicinalproduct:"{d}"' for d in drugs]
    brand_terms = [f'patient.drug.medicinalproduct:"{b}"' for b in brands]
    terms = drug_terms + brand_terms
    drug_clause = "(" + " OR ".join(terms) + ")"
    date_clause = f"(receivedate:[{start_date.replace('-', '')}+TO+{end_date.replace('-', '')}])"
    country_clause = f"(occurcountry:\"{country}\")"
    return f"{drug_clause} AND {date_clause} AND {country_clause}"


def fetch_faers(
    run_id: str,
    drugs: List[str],
    brands: List[str],
    start_date: str,
    end_date: str,
    country: str,
    out_dir: str,
) -> Dict[str, int]:
    ensure_directories()
    os.makedirs(out_dir, exist_ok=True)

    search = _build_search_query(drugs, brands, start_date, end_date, country)
    limit = OPENFDA.max_limit
    skip = 0
    total_written = 0

    out_path = os.path.join(out_dir, f"faers_{run_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("[")

        pbar = None
        first = True
        try:
            while True:
                params = {
                    "search": search,
                    "limit": limit,
                    "skip": skip,
                }
                if OPENFDA.api_key:
                    params["api_key"] = OPENFDA.api_key

                url = OPENFDA.base_url
                t0 = time.time()
                resp = requests.get(url, params=params, timeout=30)
                elapsed_ms = int((time.time() - t0) * 1000)

                result_count = 0
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    result_count = len(results)
                    if pbar is None:
                        meta_total = data.get("meta", {}).get("results", {}).get("total", 0)
                        pbar = tqdm(total=meta_total, desc="FAERS records", unit="rec")
                    if result_count == 0:
                        break
                    for record in results:
                        if not first:
                            f.write(",\n")
                        json.dump(record, f, ensure_ascii=False)
                        first = False
                        total_written += 1
                    pbar.update(result_count)
                    skip += limit
                else:
                    time.sleep(2)
                    if resp.status_code in (400, 401, 403, 404):
                        break

                append_request_log(
                    RequestLog(
                        run_id=run_id,
                        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        url=url,
                        params=params,
                        status_code=resp.status_code,
                        result_count=result_count,
                        elapsed_ms=elapsed_ms,
                    )
                )

                time.sleep(60.0 / max(1, OPENFDA.requests_per_minute))

        finally:
            if pbar is not None:
                pbar.close()
            f.write("]\n")

    manifest = {
        "run_id": run_id,
        "raw_file": out_path,
        "records": total_written,
        "sha256": sha256_file(out_path),
    }
    manifest_path = os.path.join(out_dir, f"manifest_{run_id}.json")
    write_json(manifest_path, manifest)

    return {"records": total_written, "out_file": out_path, "manifest": manifest_path}


