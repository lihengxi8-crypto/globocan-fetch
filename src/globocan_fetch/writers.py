from __future__ import annotations

import csv
import hashlib
import os
from pathlib import Path

FIELDS = [
    "country_code", "pop_label", "iso3", "pop_level", "grouping", "area_label", "who_region", "hdi_label", "income_label",
    "sex", "metric", "cancer_code", "cancer_label", "ICD", "age_start_idx", "age_end_idx", "age_label",
    "total", "total_pop", "asr", "crude_rate", "cum_risk_74", "rank",
]


def write_rows(rows: list[dict], path: Path, output_format: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".partial")
    if output_format == "csv":
        with temp.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    else:
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("Parquet output requires: pip install 'globocan-fetch[parquet]'") from exc
        pd.DataFrame(rows, columns=FIELDS).to_parquet(temp, index=False)
    os.replace(temp, path)
    return path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

