import os
from dataclasses import dataclass


@dataclass
class OpenFDAConfig:
    base_url: str = "https://api.fda.gov/drug/event.json"
    api_key: str | None = os.environ.get("OPENFDA_API_KEY")
    max_limit: int = 100
    requests_per_minute: int = 60 if api_key is None else 240


@dataclass
class RxNormConfig:
    base_url: str = "https://rxnav.nlm.nih.gov/REST"
    cache_dir: str = os.environ.get("RXNORM_CACHE_DIR", "artifacts/cache")
    cache_file: str = os.path.join(cache_dir, "rxnorm_cache.json")
    requests_per_minute: int = 60


@dataclass
class Paths:
    project_root: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    logs_dir: str = os.path.join(project_root, "logs")
    raw_faers_dir: str = os.path.join(project_root, "artifacts", "raw_faers")
    curated_tables_dir: str = os.path.join(project_root, "artifacts", "curated_tables")
    deliverables_dir: str = os.path.join(project_root, "deliverables")


OPENFDA = OpenFDAConfig()
RXNORM = RxNormConfig()
PATHS = Paths()


def ensure_directories() -> None:
    for d in [
        PATHS.logs_dir,
        PATHS.raw_faers_dir,
        PATHS.curated_tables_dir,
        PATHS.deliverables_dir,
        os.path.dirname(RXNORM.cache_file),
    ]:
        os.makedirs(d, exist_ok=True)


