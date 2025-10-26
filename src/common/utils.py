import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict, Iterable


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: str, obj: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def parse_faers_date(date_str: str | None) -> str | None:
    if not date_str:
        return None
    s = date_str.strip()
    if not s:
        return None
    try:
        if len(s) == 8 and s.isdigit():
            dt = datetime.strptime(s, "%Y%m%d")
            return dt.date().isoformat()
        if len(s) == 6 and s.isdigit():
            dt = datetime.strptime(s, "%Y%m")
            return dt.strftime("%Y-%m")
        if len(s) == 4 and s.isdigit():
            dt = datetime.strptime(s, "%Y")
            return dt.strftime("%Y")
    except Exception:
        return None
    return None


def to_bool_flag(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        v = value.strip().lower()
        return v in ("y", "yes", "true", "1")
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, bool):
        return value
    return False


