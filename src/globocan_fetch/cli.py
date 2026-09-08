from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .client import GCOClient, GCOError
from .constants import SEX_CODES, TYPE_CODES, age_combinations
from .metadata import load_or_fetch
from .writers import sha256, write_rows


def _split(value: str, allowed: dict[str, int], flag: str) -> list[str]:
    values = value.split(",")
    bad = [v for v in values if v not in allowed]
    if bad:
        raise SystemExit(f"Invalid {flag}: {', '.join(bad)}. Choose from: {', '.join(allowed)}")
    return values


def _ages(value: str) -> list[dict]:
    all_ages = age_combinations()
    if not value:
        return [next(a for a in all_ages if a["start"] == 0 and a["end"] == 17)]
    wanted = set(value.split(","))
    chosen = [a for a in all_ages if f"{a['start']}_{a['end']}" in wanted or a["label"] in wanted or a["category"] in wanted]
    if not chosen:
        raise SystemExit(f"No age ranges match --age {value}")
    return chosen


def _manifest_path(output: Path) -> Path:
    return output / "manifest.json"


def _load_manifest(output: Path) -> dict:
    path = _manifest_path(output)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"schema_version": 1, "software_version": __version__, "created_at": datetime.now(timezone.utc).isoformat(), "completed": [], "empty": [], "files": {}}


def _save_manifest(output: Path, manifest: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    temp = _manifest_path(output).with_suffix(".partial")
    temp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(_manifest_path(output))


def _rows(dataset: list[dict], pop_map: dict, cancer: dict, metric: str, sex: str, age: dict) -> list[dict]:
    out = []
    for source in dataset:
        code = source.get("country_code")
        out.append({
            "country_code": code, **pop_map.get(code, {}), "sex": sex, "metric": metric,
            "cancer_code": cancer["code"], "cancer_label": cancer["cancer_label"], "ICD": cancer["ICD"],
            "age_start_idx": age["start"], "age_end_idx": age["end"], "age_label": age["label"],
            "total": source.get("total"), "total_pop": source.get("total_pop"), "asr": source.get("asr"),
            "crude_rate": source.get("crude_rate"), "cum_risk_74": source.get("cum_risk_74", source.get("cum_risk")), "rank": source.get("rank"),
        })
    return out


def cmd_verify(args: argparse.Namespace) -> int:
    client = GCOClient(args.year, requests_per_second=args.rps)
    populations, cancers = client.populations(), client.cancers()
    print(json.dumps({"year": args.year, "population_count": len(populations), "cancer_count": len(cancers), "endpoint_base": client.base_url}, indent=2))
    return 0


def cmd_cancers(args: argparse.Namespace) -> int:
    client = GCOClient(args.year, requests_per_second=args.rps)
    for cancer in client.cancers():
        print(f"{cancer.get('cancer')}\t{cancer.get('label')}\t{cancer.get('ICD', '')}")
    return 0


def cmd_download(args: argparse.Namespace) -> int:
    if args.preset == "full":
        if not args.yes:
            raise SystemExit("Full download needs --yes (8,856 requests at current dimensions).")
        metrics, sexes, ages = list(TYPE_CODES), list(SEX_CODES), age_combinations()
    else:
        metrics, sexes, ages = _split(args.metric, TYPE_CODES, "--metric"), _split(args.sex, SEX_CODES, "--sex"), _ages(args.age)
    output = Path(args.output)
    client = GCOClient(args.year, requests_per_second=args.rps, timeout=args.timeout, retries=args.retries)
    cache_dir = output / ".globocan-fetch" / "meta"
    pop_map, cancer_map = load_or_fetch(client, cache_dir, refresh=args.refresh_meta)
    requested_cancers = [int(v) for v in args.cancer.split(",")] if args.preset != "full" else sorted(cancer_map)
    unknown = sorted(set(requested_cancers) - set(cancer_map))
    if unknown:
        raise SystemExit(f"Unknown cancer codes: {unknown}. Run `globocan-fetch cancers --year {args.year}`.")
    tasks = [(metric, sex, code, age) for metric in metrics for sex in sexes for code in requested_cancers for age in ages]
    manifest = _load_manifest(output)
    manifest.update({"year": args.year, "endpoint_base": client.base_url, "parameters": {"metrics": metrics, "sexes": sexes, "cancers": requested_cancers, "ages": ages, "format": args.format, "rps": args.rps}})
    completed, empty = set(manifest["completed"]), set(manifest["empty"])
    for index, (metric, sex, code, age) in enumerate(tasks, 1):
        key = f"{metric}/{sex}/{code}/{age['start']}_{age['end']}"
        if key in completed or key in empty:
            continue
        try:
            response = client.rates(TYPE_CODES[metric], SEX_CODES[sex], code, age["start"], age["end"])
            dataset = response["dataset"]
            if not dataset:
                manifest["empty"].append(key)
            else:
                cancer = {"code": code, **cancer_map[code]}
                suffix = "parquet" if args.format == "parquet" else "csv"
                name = f"{metric}_{sex}_can{code}_a{age['start']}-{age['end']}.{suffix}"
                path = write_rows(_rows(dataset, pop_map, cancer, metric, sex, age), output / "tables" / name, args.format)
                manifest["completed"].append(key)
                manifest["files"][str(path.relative_to(output))] = {"sha256": sha256(path), "rows": len(dataset)}
            _save_manifest(output, manifest)
            print(f"[{index}/{len(tasks)}] {key}")
        except GCOError as exc:
            _save_manifest(output, manifest)
            print(f"[{index}/{len(tasks)}] FAILED {key}: {exc}", file=sys.stderr)
    _save_manifest(output, manifest)
    print(f"Done: {len(manifest['completed'])} non-empty; {len(manifest['empty'])} empty. Manifest: {_manifest_path(output)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="globocan-fetch", description="Rate-limited GLOBOCAN Cancer Today downloader")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, func in [("verify", cmd_verify), ("cancers", cmd_cancers)]:
        p = sub.add_parser(name)
        p.add_argument("--year", type=int, default=2024)
        p.add_argument("--rps", type=float, default=1.0)
        p.set_defaults(func=func)
    download = sub.add_parser("download")
    download.add_argument("--year", type=int, default=2024)
    download.add_argument("--metric", default="incidence")
    download.add_argument("--sex", default="both")
    download.add_argument("--cancer", default="39")
    download.add_argument("--age", default="0_17")
    download.add_argument("--preset", choices=["custom", "full"], default="custom")
    download.add_argument("--yes", action="store_true")
    download.add_argument("--format", choices=["csv", "parquet"], default="parquet")
    download.add_argument("--output", required=True)
    download.add_argument("--rps", type=float, default=1.0)
    download.add_argument("--timeout", type=float, default=60)
    download.add_argument("--retries", type=int, default=4)
    download.add_argument("--refresh-meta", action="store_true")
    download.set_defaults(func=cmd_download)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except GCOError as exc:
        print(f"GCO request failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
