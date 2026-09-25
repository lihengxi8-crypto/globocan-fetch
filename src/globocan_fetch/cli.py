from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .client import GCOClient, GCOError
from .constants import SEX_CODES, TYPE_CODES, age_combinations
from .metadata import load_or_fetch
from .schema import data_dictionary_markdown
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
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest.setdefault("failed", {})
        return manifest
    return {"schema_version": 2, "software_version": __version__, "created_at": datetime.now(timezone.utc).isoformat(), "completed": [], "empty": [], "failed": {}, "files": {}}


def _save_manifest(output: Path, manifest: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    temp = _manifest_path(output).with_suffix(".partial")
    temp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(_manifest_path(output))


def _identity(year: int, endpoint_base: str, output_format: str) -> dict:
    return {"year": year, "endpoint_base": endpoint_base, "output_format": output_format, "schema_version": 2}


def _ensure_identity(manifest: dict, identity: dict) -> None:
    existing = manifest.get("dataset_identity")
    if existing and existing != identity:
        raise SystemExit("Existing output belongs to a different dataset configuration. Use a new output directory.")
    if not existing and (manifest.get("completed") or manifest.get("empty") or manifest.get("files")):
        raise SystemExit("Existing output has a legacy manifest without dataset identity. Use a new output directory.")


def _rows(dataset: list[dict], pop_map: dict, cancer: dict, metric: str, sex: str, age: dict) -> list[dict]:
    out = []
    for source in dataset:
        code = source.get("country_code")
        out.append({
            "country_code": code, **pop_map.get(code, {}), "sex": sex, "metric": metric,
            "cancer_code": cancer["code"], "cancer_label": cancer["cancer_label"], "ICD": cancer["ICD"],
            "age_start_idx": age["start"], "age_end_idx": age["end"], "age_label": age["label"],
            "total": source.get("total"), "total_pop": source.get("total_pop"), "asr": source.get("asr"),
            "crude_rate": source.get("crude_rate"), "cum_risk": source.get("cum_risk"),
            "cum_risk_74": source.get("cum_risk_74"), "rank": source.get("rank"),
        })
    return out


class ReconstructionError(GCOError):
    """Cumulative responses cannot safely yield the requested age band."""


def _population_index(dataset: list[dict], label: str) -> dict:
    indexed = {}
    for row in dataset:
        code = row.get("country_code")
        if code is None or code in indexed:
            raise ReconstructionError(f"{label}: missing or duplicate population key {code!r}")
        indexed[code] = row
    if not indexed:
        raise ReconstructionError(f"{label}: cumulative dataset is empty")
    return indexed


def _number(row: dict, field: str, code: object) -> float:
    value = row.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ReconstructionError(f"population {code}: invalid or missing {field}")
    return value


def _reconstruct_single_age_band(previous: list[dict], current: list[dict], age_index: int) -> list[dict]:
    """Reconstruct an unavailable single age band from adjacent cumulative responses."""
    if age_index not in {15, 16, 17}:
        raise ReconstructionError(f"unsupported reconstructed age index {age_index}")
    before = _population_index(previous, "lower")
    after = _population_index(current, "upper")
    if before.keys() != after.keys():
        raise ReconstructionError("cumulative population keys differ")
    reconstructed = []
    for upper in current:
        code = upper["country_code"]
        lower = before[code]
        total = _number(upper, "total", code) - _number(lower, "total", code)
        total_pop = _number(upper, "total_pop", code) - _number(lower, "total_pop", code)
        if total < 0 or total_pop <= 0:
            raise ReconstructionError(f"population {code}: negative count or nonpositive population difference")
        crude_rate = total / total_pop * 100_000
        if not math.isfinite(crude_rate):
            raise ReconstructionError(f"population {code}: nonfinite crude rate")
        # With one age stratum, the normalized World-standard weight cancels;
        # the age-standardized rate equals that stratum's age-specific rate.
        asr = crude_rate
        # IARC's standard cumulative-risk conversion assumes the age-specific
        # rate is constant over the closed five-year age band. The open-ended
        # 85+ band has no finite width and therefore has no reconstructed risk.
        cum_risk = None
        if age_index < 17:
            cumulative_rate = crude_rate * 5 / 100_000
            cum_risk = 100 * (1 - math.exp(-cumulative_rate))
        reconstructed.append({
            "country_code": code,
            "total": total,
            "total_pop": total_pop,
            "crude_rate": crude_rate,
            "asr": asr,
            "cum_risk": cum_risk,
            "cum_risk_74": None,
            "rank": None,
        })
    return reconstructed


def _check_high_age_aggregate(bands: dict[int, list[dict]], lower: list[dict], upper: list[dict]) -> None:
    """Check that all three reconstructed bands sum to the cumulative 75+ difference."""
    low, high = _population_index(lower, "0_14"), _population_index(upper, "0_17")
    indexed = {band: _population_index(rows, f"{band}_{band}") for band, rows in bands.items()}
    if set(bands) != {15, 16, 17} or any(table.keys() != low.keys() for table in [high, *indexed.values()]):
        raise ReconstructionError("75+ aggregate population keys differ")
    for code in low:
        for field in ("total", "total_pop"):
            aggregate = _number(high[code], field, code) - _number(low[code], field, code)
            summed = sum(_number(indexed[band][code], field, code) for band in (15, 16, 17))
            if not math.isclose(summed, aggregate, rel_tol=0, abs_tol=1e-7):
                raise ReconstructionError(f"population {code}: 75+ aggregate {field} mismatch")


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


def cmd_populations(args: argparse.Namespace) -> int:
    client = GCOClient(args.year, requests_per_second=args.rps)
    pop_map, _, _ = load_or_fetch(client, Path(".globocan-fetch") / str(args.year), refresh=args.refresh_meta)
    levels = sorted({row["pop_level"] for row in pop_map.values()})
    if args.level and args.level not in levels:
        raise SystemExit(f"Invalid --level {args.level}. Choose from: {', '.join(levels)}")
    print("country_code\tpop_label\tiso3\tpop_level")
    for code, row in sorted(pop_map.items()):
        if not args.level or row["pop_level"] == args.level:
            print(f"{code}\t{row.get('pop_label') or ''}\t{row.get('iso3') or ''}\t{row['pop_level']}")
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    output = Path(args.output_directory)
    path = _manifest_path(output)
    if not path.exists():
        raise SystemExit(f"No manifest.json found in {output}. Pass a standard globocan-fetch output directory.")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise SystemExit(f"Invalid manifest.json in {output}.")
    identity = manifest.get("dataset_identity", {})
    params = manifest.get("parameters", {})
    missing = [name for name in manifest.get("files", {}) if not (output / name).exists()]
    result = {"year": identity.get("year", manifest.get("year")), "software_version": manifest.get("software_version"), "endpoint": identity.get("endpoint_base", manifest.get("endpoint_base")), "format": identity.get("output_format", params.get("format")), "metrics": params.get("metrics", []), "sexes": params.get("sexes", []), "cancers": params.get("cancers", []), "age_ranges": [a.get("label") for a in params.get("ages", [])], "files_count": len(manifest.get("files", {})), "non_empty_tasks": len(manifest.get("completed", [])), "empty_tasks": len(manifest.get("empty", [])), "failed_tasks": len(manifest.get("failed", {})), "manifest_path": str(path), "missing_output_files": missing}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_download(args: argparse.Namespace) -> int:
    if args.preset == "full":
        if not args.yes:
            raise SystemExit("Full download needs --yes.")
        metrics, sexes, ages = list(TYPE_CODES), list(SEX_CODES), age_combinations()
    else:
        metrics, sexes, ages = _split(args.metric, TYPE_CODES, "--metric"), _split(args.sex, SEX_CODES, "--sex"), _ages(args.age)
    output = Path(args.output)
    client = GCOClient(args.year, requests_per_second=args.rps, timeout=args.timeout, retries=args.retries)
    cache_dir = output / ".globocan-fetch" / "meta"
    pop_map, cancer_map, metadata_info = load_or_fetch(client, cache_dir, refresh=args.refresh_meta)
    requested_cancers = [int(v) for v in args.cancer.split(",")] if args.preset != "full" else sorted(cancer_map)
    unknown = sorted(set(requested_cancers) - set(cancer_map))
    if unknown:
        raise SystemExit(f"Unknown cancer codes: {unknown}. Run `globocan-fetch cancers --year {args.year}`.")
    tasks = [(metric, sex, code, age) for metric in metrics for sex in sexes for code in requested_cancers for age in ages]
    manifest = _load_manifest(output)
    identity = _identity(args.year, client.base_url, args.format)
    _ensure_identity(manifest, identity)
    old_metadata = manifest.get("metadata")
    if old_metadata and (old_metadata["populations_sha256"] != metadata_info["populations_sha256"] or old_metadata["cancers_sha256"] != metadata_info["cancers_sha256"]) and (manifest.get("completed") or manifest.get("empty")):
        raise SystemExit("Metadata changed for an existing output. Use a new output directory.")
    manifest.update({"schema_version": 2, "dataset_identity": identity, "metadata": metadata_info, "year": args.year, "endpoint_base": client.base_url, "parameters": {"metrics": metrics, "sexes": sexes, "cancers": requested_cancers, "ages": ages, "format": args.format, "rps": args.rps}})
    if args.preset == "full":
        print(f"Full plan: {len(tasks)} requests ({len(metrics)} metrics × {len(sexes)} sexes × {len(requested_cancers)} cancer/site entries × {len(ages)} age ranges).")
    dictionary = output / "DATA_DICTIONARY.md"
    if not dictionary.exists():
        dictionary.parent.mkdir(parents=True, exist_ok=True)
        dictionary.write_text(data_dictionary_markdown(), encoding="utf-8")
    completed, empty = set(manifest["completed"]), set(manifest["empty"])
    failed = manifest["failed"]
    # Older runs recorded the empty direct 75+ response as final. Retry only
    # those known 2024 gaps; unrelated empty responses remain resumable.
    if args.year == 2024:
        retry = {f"{metric}/{sex}/{code}/{band}_{band}" for metric in metrics for sex in sexes
                 for code in requested_cancers for band in (15, 16, 17)}
        empty.difference_update(retry)
        manifest["empty"] = [key for key in manifest["empty"] if key in empty]
    rate_cache: dict[tuple[int, int, int, int, int], list[dict]] = {}
    high_age_plan: dict[tuple[str, str, int], dict[int, tuple[list[dict], dict] | GCOError] | GCOError] = {}
    all_high_bands_requested = {15, 16, 17} <= {a["start"] for a in ages if a["start"] == a["end"]}

    def fetch_rate(metric_code: int, sex_code: int, cancer_code: int, age_start: int, age_end: int) -> list[dict]:
        cache_key = (metric_code, sex_code, cancer_code, age_start, age_end)
        if cache_key not in rate_cache:
            rate_cache[cache_key] = client.rates(metric_code, sex_code, cancer_code, age_start, age_end)["dataset"]
        return rate_cache[cache_key]

    def prepare_high_ages(metric: str, sex: str, code: int) -> dict[int, tuple[list[dict], dict] | GCOError]:
        metric_code, sex_code = TYPE_CODES[metric], SEX_CODES[sex]
        direct_responses = {}
        for band in (15, 16, 17):
            try:
                direct_responses[band] = fetch_rate(metric_code, sex_code, code, band, band)
            except GCOError as exc:
                direct_responses[band] = exc
        all_empty = all(value == [] for value in direct_responses.values())
        plan = {}
        for band in (15, 16, 17):
            direct = direct_responses[band]
            if isinstance(direct, GCOError):
                plan[band] = direct
                continue
            provenance = {"source": "gco_response", "derived_fields": [], "unavailable_fields": []}
            if direct:
                plan[band] = (direct, provenance)
                continue
            try:
                lower = fetch_rate(metric_code, sex_code, code, 0, band - 1)
                upper = fetch_rate(metric_code, sex_code, code, 0, band)
                derived = _reconstruct_single_age_band(lower, upper, band)
            except GCOError as exc:
                if all_empty:
                    raise
                plan[band] = exc
                continue
            provenance = {
                "source": "derived_cumulative_difference", "direct_query": f"{band}_{band}",
                "direct_query_result": "empty", "derived_from": [f"0_{band - 1}", f"0_{band}"],
                "derived_fields": ["total", "total_pop", "crude_rate", "asr"] + (["cum_risk"] if band < 17 else []),
                "unavailable_fields": ["cum_risk_74", "rank"] + (["cum_risk"] if band == 17 else []),
            }
            plan[band] = (derived, provenance)
        if all_empty:
            _check_high_age_aggregate({band: plan[band][0] for band in (15, 16, 17)},
                                      fetch_rate(metric_code, sex_code, code, 0, 14),
                                      fetch_rate(metric_code, sex_code, code, 0, 17))
        return plan

    for index, (metric, sex, code, age) in enumerate(tasks, 1):
        key = f"{metric}/{sex}/{code}/{age['start']}_{age['end']}"
        if key in completed or key in empty:
            continue
        try:
            metric_code, sex_code = TYPE_CODES[metric], SEX_CODES[sex]
            high_age = args.year == 2024 and age["start"] == age["end"] and age["start"] in {15, 16, 17}
            if high_age and all_high_bands_requested:
                group = (metric, sex, code)
                if group not in high_age_plan:
                    try:
                        high_age_plan[group] = prepare_high_ages(metric, sex, code)
                    except GCOError as exc:
                        high_age_plan[group] = exc
                plan = high_age_plan[group]
                if isinstance(plan, GCOError):
                    raise plan
                result = plan[age["start"]]
                if isinstance(result, GCOError):
                    raise result
                dataset, provenance = result
            else:
                dataset = fetch_rate(metric_code, sex_code, code, age["start"], age["end"])
                provenance = {"source": "gco_response", "derived_fields": [], "unavailable_fields": []}
            if not dataset and high_age and not all_high_bands_requested:
                band = age["start"]
                previous = fetch_rate(metric_code, sex_code, code, 0, band - 1)
                current = fetch_rate(metric_code, sex_code, code, 0, band)
                dataset = _reconstruct_single_age_band(previous, current, band)
                provenance = {
                    "source": "derived_cumulative_difference",
                    "direct_query": f"{band}_{band}", "direct_query_result": "empty",
                    "derived_from": [f"0_{band - 1}", f"0_{band}"],
                    "derived_fields": ["total", "total_pop", "crude_rate", "asr"] + (["cum_risk"] if band < 17 else []),
                    "unavailable_fields": ["cum_risk_74", "rank"] + (["cum_risk"] if band == 17 else []),
                }
            if not dataset:
                manifest["empty"].append(key)
                empty.add(key)
            else:
                cancer = {"code": code, **cancer_map[code]}
                suffix = "parquet" if args.format == "parquet" else "csv"
                name = f"{metric}_{sex}_can{code}_a{age['start']}-{age['end']}.{suffix}"
                path = write_rows(_rows(dataset, pop_map, cancer, metric, sex, age), output / "tables" / name, args.format)
                manifest["completed"].append(key)
                completed.add(key)
                manifest["files"][str(path.relative_to(output))] = {"sha256": sha256(path), "rows": len(dataset), **provenance}
            failed.pop(key, None)
            _save_manifest(output, manifest)
            print(f"[{index}/{len(tasks)}] {key}")
        except GCOError as exc:
            failed[key] = str(exc)
            _save_manifest(output, manifest)
            print(f"[{index}/{len(tasks)}] FAILED {key}: {exc}", file=sys.stderr)
    _save_manifest(output, manifest)
    requested_keys = {f"{metric}/{sex}/{code}/{age['start']}_{age['end']}" for metric, sex, code, age in tasks}
    if requested_keys and requested_keys <= empty:
        print("Warning: all requested datasets were empty.", file=sys.stderr)
    print(f"Done: {len(manifest['completed'])} non-empty; {len(manifest['empty'])} empty; {len(failed)} failed. Manifest: {_manifest_path(output)}")
    return 2 if requested_keys & failed.keys() else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="globocan-fetch", description="Rate-limited GLOBOCAN Cancer Today downloader")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, func in [("verify", cmd_verify), ("cancers", cmd_cancers)]:
        p = sub.add_parser(name)
        p.add_argument("--year", type=int, default=2024)
        p.add_argument("--rps", type=float, default=1.0)
        p.set_defaults(func=func)
    populations = sub.add_parser("populations")
    populations.add_argument("--year", type=int, default=2024)
    populations.add_argument("--rps", type=float, default=1.0)
    populations.add_argument("--level", default="")
    populations.add_argument("--refresh-meta", action="store_true")
    populations.set_defaults(func=cmd_populations)
    inspect = sub.add_parser("inspect")
    inspect.add_argument("output_directory")
    inspect.set_defaults(func=cmd_inspect)
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
