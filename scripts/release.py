#!/usr/bin/env python3
import argparse
import os
import shutil
import time

from src.common.config import PATHS, ensure_directories
from src.common.utils import sha256_file


def create_release(deliverables_dir: str, out_dir: str) -> str:
    ensure_directories()
    os.makedirs(out_dir, exist_ok=True)

    timestamp = time.strftime("%Y-%m-%d")
    archive_name = f"release_{timestamp}"
    archive_path = os.path.join(out_dir, archive_name)


    shutil.make_archive(archive_path, "zip", deliverables_dir)
    zip_path = archive_path + ".zip"


    checksum = sha256_file(zip_path)
    checksum_path = zip_path + ".sha256"
    with open(checksum_path, "w", encoding="utf-8") as f:
        f.write(f"{checksum}  {os.path.basename(zip_path)}\n")

    print(f"Created release archive: {zip_path}")
    print(f"SHA-256: {checksum}")
    print(f"Checksum file: {checksum_path}")
    return zip_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a zipped release of deliverables")
    parser.add_argument(
        "--deliverables-dir",
        default=PATHS.deliverables_dir,
        help="Path to deliverables directory",
    )
    parser.add_argument(
        "--out",
        default=os.path.join(PATHS.project_root, "releases"),
        help="Output directory for release archive",
    )
    args = parser.parse_args()
    create_release(args.deliverables_dir, args.out)


if __name__ == "__main__":
    main()

