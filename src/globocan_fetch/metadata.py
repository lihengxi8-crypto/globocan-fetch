from __future__ import annotations

import json
from pathlib import Path

from .constants import GROUPING_TO_LEVEL


def load_or_fetch(client, cache_dir: Path, refresh: bool = False) -> tuple[dict[int, dict], dict[int, dict]]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    pop_path, cancer_path = cache_dir / "populations.json", cache_dir / "cancers.json"
    if refresh or not pop_path.exists():
        pop_path.write_text(json.dumps(client.populations(), ensure_ascii=False, indent=2), encoding="utf-8")
    if refresh or not cancer_path.exists():
        cancer_path.write_text(json.dumps(client.cancers(), ensure_ascii=False, indent=2), encoding="utf-8")
    populations, cancers = json.loads(pop_path.read_text(encoding="utf-8")), json.loads(cancer_path.read_text(encoding="utf-8"))
    pop_map: dict[int, dict] = {}
    for raw in populations:
        code = int(raw["country"])
        iso3 = raw.get("country_iso3")
        level = "country" if iso3 else "world" if code == 900 else GROUPING_TO_LEVEL.get(raw.get("grouping"), "aggregate")
        pop_map[code] = {
            "pop_label": raw.get("label"), "iso3": iso3, "pop_level": level,
            "grouping": raw.get("grouping"), "area_label": raw.get("area_label"),
            "who_region": raw.get("who_region"), "hdi_label": raw.get("hdi_label"),
            "income_label": raw.get("income_label"),
        }
    cancer_map = {int(raw["cancer"]): {"cancer_label": raw.get("label"), "ICD": raw.get("ICD")} for raw in cancers}
    return pop_map, cancer_map

