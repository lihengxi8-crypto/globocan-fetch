# globocan-fetch

Reproducible, rate-limited downloads of GLOBOCAN Cancer Today tabular estimates, with population and cancer metadata added to the result.

[中文说明](README.zh-CN.md)

> **Status:** early, research-oriented software. The GCO endpoint used here is observed from the public Cancer Today web application; it is not presented as a stable public API. Run `verify` before a project and pin the resulting manifest with your analysis.

## What it does

- Queries one `(metric, sex, cancer, age range)` combination at a time. Each query uses `populations=all`, which currently returns countries and GCO aggregate populations together.
- Downloads and caches current population and cancer metadata.
- Adds readable labels, ISO3 codes and population grouping fields.
- Uses a global request-rate limit, retries transient errors, honors `Retry-After`, and writes outputs atomically.
- Records a `manifest.json` so a download can be resumed and reported reproducibly.

It does **not** distribute GLOBOCAN data. Generated data and caches are ignored by Git.

## Install

```bash
python -m venv .venv
.venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install -e ".[parquet,dev]"
```

On Windows, replace `.venv/bin/python` with `.venv\\Scripts\\python`.

## Start small

```bash
# Confirm the observed endpoints and see available metadata.
globocan-fetch verify --year 2024
globocan-fetch cancers --year 2024

# Female breast-cancer incidence, all ages, all populations.
globocan-fetch download \
  --year 2024 --metric incidence --sex female --cancer 20 --age 0_17 \
  --format parquet --output data/breast_female_2024
```

The output contains `data.parquet` (or `data.csv`) and `manifest.json`.

## Full download

A full run currently represents 8,856 endpoint requests: 2 metrics × 3 sexes × 41 cancers × 36 age combinations. It is deliberately opt-in:

```bash
globocan-fetch download --year 2024 --preset full --yes --output data/globocan_2024
```

Use conservative settings for shared public infrastructure; the defaults target one request per second across all workers. Increase only with permission from the data provider.

## Query controls

```bash
globocan-fetch download --year 2024 \
  --metric incidence,mortality --sex both,female --cancer 20,39 \
  --age 0_2,0_17 --format csv --output data/example
```

Age indices map to five-year groups: `0=0–4`, …, `17=85+`. Both `0_17` and the label `0-85+` are accepted. `--age cumulative` selects the 18 cumulative ranges; `--age five_year` selects the 18 individual groups.

## Data fields

Each row represents one population for one requested metric/sex/cancer/age combination. Added fields include `pop_label`, `iso3`, `pop_level`, `cancer_label`, `ICD`, and `age_label`. Source fields include `total`, `total_pop`, `asr`, `crude_rate`, `cum_risk_74`, and `rank` where available.

Do not add age-standardized rates across age bands. Cases and populations can be summed to derive a crude rate; ASR must be recalculated using the appropriate standard-population weights.

## Reproducibility and responsible use

The command manifest stores parameters, endpoint base, software version, metadata timestamps, completed task keys, empty-result keys and output hashes. Keep it with derived tables and report the GCO access date/version in publications.

GLOBOCAN/IARC/WHO data and website materials have their own terms, attribution and redistribution conditions. This repository's MIT license covers **only this code**. Before sharing downloaded data, releases, or derivative databases, check the current GCO/IARC terms of use and cite the official GCO source.

## Development

```bash
python -m pytest
python -m globocan_fetch.cli --help
```

See [docs/api-observations.md](docs/api-observations.md) for the request model and [docs/release-checklist.md](docs/release-checklist.md) before publishing.
