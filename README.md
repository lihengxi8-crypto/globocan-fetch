# globocan-fetch

A reproducible downloader and data guide for [GLOBOCAN Cancer Today](https://gco.iarc.who.int/today/) tabular estimates.

`globocan-fetch` helps researchers retrieve, document, understand, and analyze selected GLOBOCAN **incidence and mortality estimates** in CSV or Parquet format.

[中文说明](README.zh-CN.md)

> **Project status: v0.2, research-oriented software.**  
> `globocan-fetch` is not an official IARC, WHO, or GCO tool. It uses request paths observed from the public Cancer Today web application; these endpoints should not be assumed to be a stable public API. The repository contains code only and does not distribute downloaded GLOBOCAN data.

---

<!-- section: what-is-globocan -->
## 1. What is GLOBOCAN?

GLOBOCAN is part of the International Agency for Research on Cancer (IARC) Global Cancer Observatory. Cancer Today provides estimates of the cancer burden across countries and other population groupings.

The most important point for first-time users is that **GLOBOCAN is an estimation dataset**.

It is not:

- a patient-level database;
- a collection of individual medical records;
- a raw export of all national cancer registry cases;
- a substitute for registry microdata.

Values such as `total` represent **estimated numbers of new cancer cases or deaths** for the requested population, sex, cancer site, and age range.

A GLOBOCAN **data year** and the date on which you access the data are different concepts. The same nominal data year may also be accompanied by a later release or update date. At the time this documentation was prepared, Cancer Today displayed **GLOBOCAN 2024 – 08.07.2026**. Always check the current Cancer Today website when reporting the official version used in a study.

For reproducible research, record at least:

- GLOBOCAN data year;
- official Cancer Today version or release information when available;
- access/download date;
- cancer definition;
- sex;
- age range;
- metric;
- analysis code and the `globocan-fetch` manifest.

---

<!-- section: what-is-globocan-fetch -->
## 2. What is globocan-fetch?

`globocan-fetch` is a small command-line tool for reproducible retrieval of Cancer Today tabular estimates.

It is useful when the same GLOBOCAN queries need to be repeated, documented, or analyzed programmatically.

The tool:

- queries selected combinations of metric, sex, cancer/site, and age range;
- currently uses `populations=all`, so one query can return countries together with GCO aggregate populations;
- downloads and caches population and cancer metadata;
- adds readable population and cancer labels to the returned rows;
- applies a conservative global request-rate limit;
- retries transient request failures;
- writes CSV or Parquet output;
- maintains a resumable `manifest.json`;
- records output file hashes and metadata hashes;
- writes a bilingual `DATA_DICTIONARY.md`.

The official Cancer Today website remains the authoritative place to:

- visually explore the estimates;
- check current presentation and terminology;
- inspect the current GLOBOCAN release/version;
- review IARC/GCO terms of use.

`globocan-fetch` is **not another cancer database** and does not alter GLOBOCAN estimates.

---

<!-- section: supported-data -->
## 3. What data are supported?

### Metrics

The current version supports:

- `incidence`
- `mortality`

Cancer Today contains other views and indicators that are currently outside the scope of `globocan-fetch`.

### Sex

Supported values are:

- `both`
- `male`
- `female`

### Cancer/site entries

Cancer definitions are read from the Cancer Today metadata endpoint for the requested year.

For GLOBOCAN 2024, the currently observed metadata contains **41 cancer/site entries**. This does **not** mean that GLOBOCAN contains 41 mutually exclusive individual cancer types.

The metadata also contains composite or summary entries such as:

- All cancers;
- All cancers excluding non-melanoma skin cancer;
- Colorectum;
- Other specified cancers;
- Unspecified sites.

Use the runtime metadata rather than relying on a manually maintained list:

```bash
globocan-fetch cancers --year 2024
```

### Populations

A returned table can contain:

- individual countries;
- World;
- continents;
- UN subregions;
- WHO regions;
- HDI groups;
- World Bank income groups;
- GICR hub regions;
- other GCO aggregate populations.

This means that **country rows and aggregate rows coexist in the same output**.

### Age ranges

The tool supports:

- predefined cumulative age ranges;
- individual five-year age groups.

Age groups use zero-based indices from `0` to `17`.

---

<!-- section: quick-start -->
## 4. Quick start

### Install

Python 3.10 or newer is recommended.

macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[parquet]"
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[parquet]"
```

Check the CLI:

```bash
globocan-fetch --help
```

Before starting a research project, verify that the currently observed endpoints and metadata are still usable:

```bash
globocan-fetch verify --year 2024
globocan-fetch cancers --year 2024
globocan-fetch populations --year 2024
```

### First download

Example: 2024 female breast-cancer incidence, age 0–85+, all returned populations.

```bash
globocan-fetch download \
  --year 2024 \
  --metric incidence \
  --sex female \
  --cancer 20 \
  --age 0_17 \
  --format parquet \
  --output data/breast_female_2024
```

For CSV:

```bash
globocan-fetch download \
  --year 2024 \
  --metric incidence \
  --sex female \
  --cancer 20 \
  --age 0_17 \
  --format csv \
  --output data/breast_female_2024_csv
```

The default request rate is deliberately conservative. Do not increase request frequency aggressively on shared public infrastructure.

---

<!-- section: understanding-output -->
## 5. Understanding the output

A standard output directory looks like:

```text
data/breast_female_2024/
├── tables/
│   └── incidence_female_can20_a0-17.parquet
├── DATA_DICTIONARY.md
├── manifest.json
└── .globocan-fetch/
    └── meta/
        ├── populations.json
        └── cancers.json
```

### `tables/`

Contains the analysis-ready CSV or Parquet files.

**One output table fixes one `metric × sex × cancer × age range` combination. Each row represents one population, not one patient.**

For example:

```text
incidence_female_can20_a0-17.parquet
```

contains female breast-cancer incidence estimates for the queried age range, with separate rows for the populations returned by GCO.

### `manifest.json`

The manifest is part of the reproducible data snapshot.

It records information including:

- software version;
- dataset identity;
- GLOBOCAN year;
- observed endpoint base;
- output format;
- query parameters;
- completed query tasks;
- empty query tasks;
- output file row counts;
- output SHA-256 hashes;
- population metadata SHA-256;
- cancer metadata SHA-256;
- timestamps.

Keep the manifest with your analysis code and derived data.

### `DATA_DICTIONARY.md`

A bilingual field guide generated from the same schema used to write the data files.

It explains every public output column and helps keep data documentation synchronized with the software.

### `.globocan-fetch/meta/`

Contains the population and cancer metadata used for that output snapshot.

These files are part of the retrieval context and should not be casually replaced after results have already been downloaded.

---

<!-- section: file-naming -->
## 6. File naming

Example:

```text
incidence_female_can20_a0-17.parquet
```

| Part | Meaning |
|---|---|
| `incidence` | Metric |
| `female` | Sex |
| `can20` | GCO Cancer Today cancer/site code 20 |
| `a0-17` | Age indices 0 through 17 |
| `parquet` | Output format |

A common source of confusion is `can20`.

`can20` means **GCO cancer/site entry 20**. It does not mean ICD-10 `C20`.

For the currently observed GLOBOCAN 2024 metadata:

```text
GCO cancer/site code 20 -> Breast -> ICD C50
```

Always use the cancer metadata when interpreting `cancer_code`.

---

<!-- section: data-dictionary -->
## 7. Data dictionary

Each output row represents one population for one requested metric, sex, cancer/site, and age range.

The public schema contains 23 fields.

| Field | Source | Meaning | Unit / Values | Notes |
|---|---|---|---|---|
| `country_code` | GCO response | GCO population code for the returned row | Numeric code | Countries commonly use corresponding numeric population codes; aggregate populations have their own GCO codes. Do not assume every row is a country. |
| `pop_label` | GCO population metadata | Human-readable population label | Text | Examples include `China`, `World`, `Eastern Asia`, or an HDI group. |
| `iso3` | GCO population metadata | ISO3 country code | e.g. `CHN`, `USA`; nullable | Normally populated for countries and empty for aggregate populations. |
| `pop_level` | Derived by globocan-fetch | Standardized population level | `country`, `world`, `continent`, `subregion`, `who`, `hdi`, `income`, `hub`, `other`, or fallback `aggregate` | Derived from GCO population metadata; not a raw rate-response field. |
| `grouping` | GCO population metadata | GCO metadata grouping/category | Text; nullable | Do not interpret this field simply as “continent”; its meaning follows the source metadata. |
| `area_label` | GCO population metadata | Geographic or area label provided by GCO metadata | Text; nullable | May identify a regional grouping such as an UN subregion. |
| `who_region` | GCO population metadata | WHO region identifier | e.g. AFRO, EURO, WPRO; nullable | Metadata classification, not an epidemiological estimate. |
| `hdi_label` | GCO population metadata | HDI-group label | Text; nullable | A category label, not a country's numeric HDI value. |
| `income_label` | GCO population metadata | World Bank income-group label | Text; nullable | A classification label, not numeric income. |
| `sex` | Query / normalized | Requested sex | `both`, `male`, `female` | Fixed for a given output table. |
| `metric` | Query / normalized | Requested cancer-burden metric | `incidence`, `mortality` | Fixed for a given output table. |
| `cancer_code` | GCO cancer metadata | Cancer Today cancer/site entry code | Integer | Not an ICD code. |
| `cancer_label` | GCO cancer metadata | Human-readable cancer/site label | Text | Example: `Breast`. |
| `ICD` | GCO cancer metadata | ICD definition associated with the GCO cancer/site entry | Text / code range | May be a single ICD code or a composite range. |
| `age_start_idx` | Query / derived | Starting five-year age-group index | `0`–`17` | Zero-based. |
| `age_end_idx` | Query / derived | Ending five-year age-group index | `0`–`17` | Inclusive. |
| `age_label` | Derived by globocan-fetch | Human-readable queried age range | e.g. `0-85+`, `65-69` | Describes the age range requested for the table. |
| `total` | GCO response | Estimated number of incident cases or deaths | Count | Incidence tables contain estimated new cases; mortality tables contain estimated deaths. This is not a rate. |
| `total_pop` | GCO response | Population denominator corresponding to the queried sex and age range | Persons | Used when interpreting or deriving crude rates. |
| `asr` | GCO response | Age-Standardized Rate (World) | Usually per 100,000 | Do not add ASRs across age bands. |
| `crude_rate` | GCO response | Crude rate | Usually per 100,000 | Conceptually related to `total / total_pop × 100,000`; API rounding may produce small differences. |
| `cum_risk_74` | GCO response | Estimated cumulative risk from birth through age 74, i.e. before age 75 | Percent (%) | May be missing for some responses. **It does not represent risk over the table's `age_label` interval.** |
| `rank` | GCO response | Ranking value returned by the current API context | Integer / nullable | Context-dependent; do not interpret it as a universal fixed global rank outside the original query. |

<!-- concept: cum-risk-0-74 -->

`cum_risk_74` is specifically an estimate for **ages 0–74 / before age 75**. It must not be reinterpreted as the cumulative risk for whatever range appears in `age_label`.

---

<!-- section: measures -->
## 8. Understanding GLOBOCAN measures

### Estimated count: `total`

For incidence:

```text
total = estimated number of new cancer cases
```

For mortality:

```text
total = estimated number of cancer deaths
```

These are GLOBOCAN estimates, not necessarily the exact number of individually observed registry records.

### Crude rate

The crude rate relates the estimated event count to the corresponding population.

Conceptually:

```text
crude rate ≈ total / total_pop × 100,000
```

Crude rates are influenced by the age structure of a population.

### Age-Standardized Rate (World): `asr`

ASR applies age standardization to improve descriptive comparison between populations with different age structures.

It is commonly reported per 100,000 people.

<!-- concept: asr-not-additive -->

**ASRs from separate age bands or age ranges must not be added together.**

If you combine five-year age groups, you may sum counts and population denominators to derive a crude rate. Recalculation of an ASR requires appropriate standard-population weights.

`globocan-fetch` does not currently provide an automatic arbitrary-age-range ASR recalculation workflow.

### Cumulative risk 0–74: `cum_risk_74`

This value represents the estimated cumulative risk from birth through age 74, expressed as a percentage.

It is **not** determined by the table's `age_label`.

---

<!-- section: population-hierarchy -->
## 9. Population hierarchy

`globocan-fetch` derives `pop_level` from GCO population metadata to make mixed country/aggregate output easier to work with.

Possible levels include:

| `pop_level` | Meaning |
|---|---|
| `country` | Individual country |
| `world` | World |
| `continent` | Continental aggregate |
| `subregion` | UN or similar regional aggregate |
| `who` | WHO region |
| `hdi` | HDI grouping |
| `income` | World Bank income grouping |
| `hub` | GICR hub grouping |
| `other` | Other recognized aggregate category |
| `aggregate` | Fallback for an aggregate not mapped to a known level |

<!-- concept: country-filter -->

Before performing a country ranking, country-level correlation, or country scatter plot, filter explicitly:

```python
countries = df[df["pop_level"] == "country"]
```

Otherwise, rows such as World, continents, WHO regions, HDI groups, and income groups may be mixed into a country-level analysis.

To inspect current population metadata:

```bash
globocan-fetch populations --year 2024
globocan-fetch populations --year 2024 --level country
globocan-fetch populations --year 2024 --level hdi
```

---

<!-- section: cancer-definitions -->
## 10. Cancer definitions

GCO `cancer_code` and ICD codes are different identifiers.

<!-- concept: cancer-code-not-icd -->

```text
cancer_code ≠ ICD
```

For example:

```text
GCO cancer/site code 20 -> Breast -> C50
```

The cancer/site code identifies an entry in the Cancer Today metadata. The `ICD` field describes the ICD definition associated with that entry.

Some entries are composite or summary categories rather than a single anatomical cancer site.

Do not maintain a hard-coded cancer list in analysis scripts when it can be avoided. Inspect the metadata for the data year you are using:

```bash
globocan-fetch cancers --year 2024
```

---

<!-- section: age-groups -->
## 11. Age groups

Cancer Today age queries use zero-based indices for five-year age groups:

| Index | Age |
|---:|---|
| 0 | 0–4 |
| 1 | 5–9 |
| 2 | 10–14 |
| 3 | 15–19 |
| 4 | 20–24 |
| 5 | 25–29 |
| 6 | 30–34 |
| 7 | 35–39 |
| 8 | 40–44 |
| 9 | 45–49 |
| 10 | 50–54 |
| 11 | 55–59 |
| 12 | 60–64 |
| 13 | 65–69 |
| 14 | 70–74 |
| 15 | 75–79 |
| 16 | 80–84 |
| 17 | 85+ |

Examples:

```text
0_14   -> 0–74
0_17   -> 0–85+
13_13  -> 65–69
```

A query such as:

```text
0_17
```

does **not** return 18 age rows.

It requests one aggregate result for the entire age range from 0 through 85+, with separate rows for populations.

If you need separate five-year age groups, request the individual five-year ranges.

The CLI also supports predefined categories such as:

```bash
--age cumulative
--age five_year
```

---

<!-- section: analysis-recipes -->
## 12. Analysis recipes

### Read Parquet

```python
import pandas as pd

df = pd.read_parquet(
    "data/breast_female_2024/tables/incidence_female_can20_a0-17.parquet"
)
```

### Read CSV

```python
import pandas as pd

df = pd.read_csv(
    "data/breast_female_2024_csv/tables/incidence_female_can20_a0-17.csv"
)
```

### Keep countries only

```python
countries = df[df["pop_level"] == "country"]
```

### Select World

```python
world = df[df["pop_level"] == "world"]
```

or, when appropriate:

```python
world = df[df["country_code"] == 900]
```

### Select China

```python
china = df[df["iso3"] == "CHN"]
```

### Rank countries by ASR

```python
ranking = (
    df[df["pop_level"] == "country"]
    .sort_values("asr", ascending=False)
    [["pop_label", "total", "asr"]]
)
```

### Work with five-year age tables

If you downloaded individual five-year groups, concatenate the required files or read them into a long table and filter by `age_start_idx`, `age_end_idx`, or `age_label`.

### Aggregate counts and derive a crude rate

For a selected population/cancer/sex/metric across several non-overlapping five-year age groups:

```python
agg = (
    df.groupby(["country_code", "pop_label"], as_index=False)
    .agg(
        total=("total", "sum"),
        total_pop=("total_pop", "sum"),
    )
)

agg["crude_rate"] = agg["total"] / agg["total_pop"] * 100_000
```

**Do not sum ASR.**

Recalculating an ASR requires the appropriate standard-population weights.

---

<!-- section: common-pitfalls -->
## 13. Common pitfalls

1. **Mixing countries and aggregate populations.**  
   Use `pop_level == "country"` for country-only analyses.

2. **Adding ASRs.**  
   ASRs from separate age bands cannot be summed.

3. **Treating `total` as an observed registry count.**  
   GLOBOCAN provides estimated cancer-burden counts.

4. **Confusing `cancer_code` with ICD.**  
   `cancer_code` is a Cancer Today metadata entry code.

5. **Treating `hdi_label` as numeric HDI.**  
   It is a category label.

6. **Treating `income_label` as numeric income.**  
   It is an income-group classification.

7. **Assuming one table represents one country.**  
   One table represents one query combination; rows represent populations.

8. **Assuming every sex/cancer combination returns data.**  
   Sex-specific cancers can produce empty datasets for incompatible queries.

9. **Interpreting `cum_risk_74` as the current age-range risk.**  
   It refers to cumulative risk through age 74.

10. **Confusing data year with access date.**  
    A 2024 estimate may be downloaded or updated later.

11. **Assuming a data year identifies the complete release context.**  
    Check the current official Cancer Today release/version information.

12. **Assuming the observed endpoint is permanent.**  
    The web application's request model may change.

---

<!-- section: reproducibility -->
## 14. Reproducibility

Each download directory contains a `manifest.json`.

Manifest schema v2 records the identity and state of the local data snapshot, including:

- software version;
- schema version;
- GLOBOCAN year;
- observed endpoint base;
- output format;
- query parameters;
- completed tasks;
- empty tasks;
- output file row counts;
- output SHA-256 hashes;
- population metadata SHA-256;
- cancer metadata SHA-256;
- timestamps.

The tool protects against several forms of accidental mixing.

If an existing output directory belongs to a different year, endpoint, output format, or schema identity, the download is rejected rather than silently reusing completed task keys.

If metadata are refreshed after results already exist and the new metadata hashes differ from those stored in the snapshot, the tool also refuses to continue writing into that directory.

Use a new output directory when the underlying retrieval context changes.

You can inspect a completed local snapshot without making network requests:

```bash
globocan-fetch inspect data/breast_female_2024
```

Keep the manifest with:

- analysis scripts;
- derived datasets;
- statistical outputs;
- project documentation.

The manifest records the local retrieval context, but it should not be treated as a substitute for checking the official Cancer Today release/version when preparing a publication.

---

<!-- section: technical-notes -->
## 15. Technical notes

The currently observed request model is based on endpoints used by the public Cancer Today web application.

Conceptually, the tool accesses metadata and rate endpoints under:

```text
https://gco.iarc.fr/gateway_prod/api/globocan/v3/{year}/
```

Observed metadata resources include:

```text
meta/populations/all/
meta/cancers/all/
```

Rate requests currently follow a pattern equivalent to:

```text
data/rate/{metric_code}/{sex_code}/all/{cancer_code}/
    ?ages_group={start_idx}_{end_idx}
```

Current normalized mappings include:

```text
incidence -> 0
mortality -> 1

both   -> 0
male   -> 1
female -> 2
```

The fact that these endpoints are observable from the web application does not mean that IARC guarantees them as a stable public API.

Run:

```bash
globocan-fetch verify --year 2024
```

before beginning a new retrieval project.

For lower-level implementation notes, see:

```text
docs/api-observations.md
```

A full preset is calculated from the runtime dimensions:

```text
metrics × sexes × cancer/site metadata entries × age combinations
```

For the currently verified GLOBOCAN 2024 metadata, this corresponds to 8,856 query combinations. That number should not be assumed to apply to every year.

---

<!-- section: citation-terms -->
## 16. Citation and terms

GLOBOCAN data, Cancer Today website materials, and related IARC/WHO resources are governed by their own attribution, use, and redistribution conditions.

The MIT license in this repository applies to the **software code**, not to downloaded GLOBOCAN data.

Before publishing or redistributing downloaded or derived data:

1. review the current GCO/IARC terms of use;
2. cite the official GLOBOCAN / Global Cancer Observatory source;
3. report the data year and relevant release/version information;
4. report the access date;
5. preserve enough query and analysis information for reproducibility.

This repository does not distribute a full copy of GLOBOCAN data and should not be used as a public mirror of the Cancer Today dataset.

For software citation information, see:

```text
CITATION.cff
```

---

## Development

To install development dependencies:

```bash
python -m pip install -e ".[parquet,dev]"
```

Run tests:

```bash
pytest
```

The repository test suite is designed to run without downloading the full GLOBOCAN dataset.