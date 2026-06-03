from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_ROOT = PROJECT_ROOT / "configs"
RESOURCE_ROOT = PROJECT_ROOT / "resources"


@lru_cache(maxsize=32)
def load_language_pair(pair: str) -> dict[str, Any]:
    path = CONFIG_ROOT / "language_pairs" / f"{pair}.yaml"
    if not path.exists():
        available = sorted(p.stem for p in (CONFIG_ROOT / "language_pairs").glob("*.yaml"))
        raise FileNotFoundError(f"Unknown language pair '{pair}'. Available: {available}")

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    data.setdefault("pair", pair)
    data.setdefault("evaluation_dimensions", [])
    data.setdefault("domains", [])
    return data


def load_terminology(pair: str, domain: str) -> list[dict[str, str]]:
    base = RESOURCE_ROOT / "terminology" / pair
    candidates = list(dict.fromkeys([base / f"{domain}.csv", base / "general.csv"]))
    rows: list[dict[str, str]] = []

    for path in candidates:
        if not path.exists():
            continue
        import csv

        with path.open("r", encoding="utf-8-sig", newline="") as file:
            rows.extend(dict(row) for row in csv.DictReader(file))

    return rows
