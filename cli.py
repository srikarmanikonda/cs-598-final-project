import argparse
import os
import sys
import shutil
from pathlib import Path
from typing import List

from src.acquire.faers_client import fetch_faers
from src.common.config import PATHS, ensure_directories
from src.common.logging_utils import new_run_id, write_run_metadata
from src.process.curate import curate_tables


def cmd_acquire(args: argparse.Namespace) -> None:
    ensure_directories()
    run_id = args.run_id or new_run_id()
    drugs = [s.strip() for s in (args.drugs or "").split(",") if s.strip()]
    brands = [s.strip() for s in (args.brands or "").split(",") if s.strip()]
    meta = {
        "run_id": run_id,
        "source": "openFDA FAERS",
        "window": {"from": args.from_date, "to": args.to_date, "country": args.country},
        "drugs": drugs,
        "brands": brands,
        "out": args.out,
    }
    write_run_metadata(run_id, meta)
    stats = fetch_faers(
        run_id=run_id,
        drugs=drugs,
        brands=brands,
        start_date=args.from_date,
        end_date=args.to_date,
        country=args.country,
        out_dir=args.out,
    )
    print(f"Run {run_id}: fetched {stats['records']} records -> {stats['out_file']}")
    if "manifest" in stats:
        print(f"Manifest: {stats['manifest']}")


def cmd_process(args: argparse.Namespace) -> None:
    ensure_directories()
    raw_path = args.raw_file
    out_dir = args.out_dir
    result = curate_tables(raw_path, out_dir)
    print("Wrote:")
    for k, v in result.items():
        print(f"- {k}: {v}")

    repo_root = Path(PATHS.project_root)
    for src_rel in ["CODEBOOK.md", "DATACITE.json", "notebooks/analysis.ipynb"]:
        src = repo_root / src_rel
        if src.exists():
            shutil.copy2(src, Path(out_dir) / ("Analysis.ipynb" if src.name.endswith("analysis.ipynb") else src.name))



def main() -> None:
    parser = argparse.ArgumentParser(description="GLP-1 FAERS curation pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    p_acq = sub.add_parser("acquire", help="Fetch FAERS raw JSON")
    p_acq.add_argument("--from", dest="from_date", required=True, help="Start date YYYY-MM-DD")
    p_acq.add_argument("--to", dest="to_date", required=True, help="End date YYYY-MM-DD")
    p_acq.add_argument("--country", default="US")
    p_acq.add_argument("--drugs", default="semaglutide,tirzepatide")
    p_acq.add_argument("--brands", default="Ozempic,Mounjaro")
    p_acq.add_argument("--out", dest="out", default=PATHS.raw_faers_dir)
    p_acq.add_argument("--run-id", dest="run_id")
    p_acq.set_defaults(func=cmd_acquire)

    p_proc = sub.add_parser("process", help="Process raw JSON into curated CSVs")
    p_proc.add_argument("--raw-file", required=True, help="Path to raw JSON array file")
    p_proc.add_argument("--out-dir", required=False, default=PATHS.deliverables_dir, help="Output directory for deliverables (default: deliverables/)")
    p_proc.set_defaults(func=cmd_process)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()


