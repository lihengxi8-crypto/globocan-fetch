from __future__ import annotations

import csv
import hashlib
import os
from pathlib import Path
from .schema import FIELD_NAMES


def write_rows(rows: list[dict], path: Path, output_format: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".partial")
    if output_format == "csv":
        with temp.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELD_NAMES, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    else:
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("Parquet output requires: pip install 'globocan-fetch[parquet]'") from exc
        pd.DataFrame(rows, columns=FIELD_NAMES).to_parquet(temp, index=False)
    os.replace(temp, path)
    return path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
