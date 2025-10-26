import json
import os
import time
from typing import Dict, Optional

import requests

from src.common.config import RXNORM, ensure_directories


class RxNormClient:
    def __init__(self) -> None:
        ensure_directories()
        self.cache: Dict[str, Dict[str, str]] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        if os.path.exists(RXNORM.cache_file):
            try:
                with open(RXNORM.cache_file, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
            except Exception:
                self.cache = {}

    def _save_cache(self) -> None:
        tmp = RXNORM.cache_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
        os.replace(tmp, RXNORM.cache_file)

    def get_rxcui(self, name: str) -> Optional[str]:
        key = name.strip().lower()
        if not key:
            return None
        if key in self.cache:
            return self.cache[key].get("rxcui")

        url = f"{RXNORM.base_url}/rxcui.json"
        params = {"name": name}
        resp = requests.get(url, params=params, timeout=20)
        if resp.status_code != 200:
            time.sleep(60.0 / max(1, RXNORM.requests_per_minute))
            return None
        data = resp.json()
        rxcui = None
        id_group = data.get("idGroup", {})
        ids = id_group.get("rxnormId", [])
        if isinstance(ids, list) and ids:
            rxcui = ids[0]
        self.cache[key] = {"rxcui": rxcui or ""}
        self._save_cache()
        time.sleep(60.0 / max(1, RXNORM.requests_per_minute))
        return rxcui


