import json
import os
import time
from typing import Dict, Optional, Tuple

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

    def _throttle(self) -> None:
        time.sleep(60.0 / max(1, RXNORM.requests_per_minute))

    def get_rxcui(self, name: str) -> Optional[str]:
        key = name.strip().lower()
        if not key:
            return None
        if key in self.cache and "rxcui" in self.cache[key]:
            return self.cache[key].get("rxcui") or None

        url = f"{RXNORM.base_url}/rxcui.json"
        params = {"name": name}
        resp = requests.get(url, params=params, timeout=20)
        if resp.status_code != 200:
            self._throttle()
            return None
        data = resp.json()
        rxcui = None
        id_group = data.get("idGroup", {})
        ids = id_group.get("rxnormId", [])
        if isinstance(ids, list) and ids:
            rxcui = ids[0]
        if key not in self.cache:
            self.cache[key] = {}
        self.cache[key]["rxcui"] = rxcui or ""
        self._save_cache()
        self._throttle()
        return rxcui

    def get_ingredient(self, rxcui: str) -> Tuple[Optional[str], Optional[str]]:

        if not rxcui:
            return (None, None)
        cache_key = f"_ing_{rxcui}"
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            ing_rxcui = entry.get("ingredient_rxcui") or None
            ing_name = entry.get("ingredient_name") or None
            return (ing_rxcui, ing_name)

        url = f"{RXNORM.base_url}/rxcui/{rxcui}/related.json"
        params = {"tty": "IN"}
        try:
            resp = requests.get(url, params=params, timeout=20)
        except Exception:
            self._throttle()
            return (None, None)
        if resp.status_code != 200:
            self._throttle()
            return (None, None)

        data = resp.json()
        ing_rxcui = None
        ing_name = None
        related_group = data.get("relatedGroup", {})
        concept_groups = related_group.get("conceptGroup", [])
        for cg in concept_groups:
            if cg.get("tty") == "IN":
                props = cg.get("conceptProperties", [])
                if props:
                    ing_rxcui = props[0].get("rxcui")
                    ing_name = props[0].get("name")
                break

        self.cache[cache_key] = {
            "ingredient_rxcui": ing_rxcui or "",
            "ingredient_name": ing_name or "",
        }
        self._save_cache()
        self._throttle()
        return (ing_rxcui, ing_name)
