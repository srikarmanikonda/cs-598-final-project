import json
import os
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

from .config import PATHS, ensure_directories


@dataclass
class RequestLog:
    run_id: str
    timestamp: str
    url: str
    params: Dict[str, Any]
    status_code: int
    result_count: int
    elapsed_ms: int


def new_run_id() -> str:
    return time.strftime("%Y%m%dT%H%M%S") + f"_{uuid.uuid4().hex[:8]}"


def _log_file(run_id: str) -> str:
    ensure_directories()
    return os.path.join(PATHS.logs_dir, f"requests_{run_id}.jsonl")


def append_request_log(entry: RequestLog) -> None:
    path = _log_file(entry.run_id)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")


def write_run_metadata(run_id: str, metadata: Dict[str, Any]) -> str:
    ensure_directories()
    path = os.path.join(PATHS.logs_dir, f"run_{run_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    return path


