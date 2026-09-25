# API observations

This project currently observes these endpoints from the GCO Cancer Today front end:

```text
GET https://gco.iarc.fr/gateway_prod/api/globocan/v3/{year}/meta/populations/all/
GET https://gco.iarc.fr/gateway_prod/api/globocan/v3/{year}/meta/cancers/all/
GET https://gco.iarc.fr/gateway_prod/api/globocan/v3/{year}/data/rate/
    {type}/{sex}/all/{cancer}/?ages_group={start}_{end}
```

Mappings:

| Dimension | Values |
| --- | --- |
| `type` | `0` incidence; `1` mortality |
| `sex` | `0` both; `1` male; `2` female |
| `cancer` | Read from the cancer metadata endpoint |
| age index | `0` (0–4) through `17` (85+) |

The client sends an ordinary browser-like `User-Agent`, `Accept: application/json`, and the Cancer Today table-page `Referer`, because that is what the web app expects. These are implementation observations, not a claim of an API contract. Endpoint availability, fields, rate limits and terms may change.

## High-age rate response observed on 24 September 2026

For 2024 female breast-cancer incidence (`type=0`, `sex=2`, `cancer=20`), `ages_group=14_14` returned HTTP 200 with 238 dataset rows. Each of `15_15`, `16_16`, and `17_17` returned HTTP 200 with `{"dataset": [], "extra": [], "error": []}`. The same three ages were empty in a separate male lung-cancer mortality CLI query (`type=1`, `sex=1`, `cancer=15`).

Adding matching `age_start` and `age_end` query parameters to each breast-cancer request produced the same row counts. Repeating `ages_group`-only requests against the current frontend's `https://gco-api.iarc.fr/api/globocan/v3/2024/` base produced the same pattern. The current frontend's URL builder uses `ages_group` for its table requests, although the tested table `data/population` endpoint returns a different population-series response and is not a drop-in replacement for this client's rate tables.

These observations establish the empty rate responses for the tested combinations. They do not establish whether another endpoint can supply equivalent 75+ cancer-rate tables or why the rate endpoint returns empty data. The client continues to record HTTP 200 with an empty dataset as `empty`, while request errors are recorded under `failed`.

## Cumulative-risk fields and high-age reconstruction (rechecked 25 September 2026)

### Official method versus field interpretation

IARC's epidemiology material defines cumulative risk over a specified age span as the probability of developing (or dying from) the disease in the absence of other causes of death. Cumulative rate sums age-specific rates across each year in that span; with five-year rates, the usual calculation assumes a constant rate within each five-year band. If cumulative rate is expressed as a percent, the conversion is `risk (%) = 100 × (1 − exp(−cumulative_rate / 100))`; when age-specific rates are per 100,000, the five-year group's cumulative rate in percent is `5 × rate / 1000`. See the [IARC Cancer Incidence in Five Continents methods](https://publications.iarc.fr/_publications/media/download/6371/8015478d4d1381e2d10b7df95e6762987b34a20e.pdf).

This is the officially documented epidemiologic method. We did not find an IARC/GLOBOCAN 2024 field-level definition specifying exactly what its JSON key `cum_risk_74` means. The description below is therefore an interpretation of observed API behavior, not an official API contract.

### Raw API behavior

The following values are from raw `dataset` rows, without `_rows()` conversion. Every listed query returned 238 population rows. `MISSING` means that the row had no such key; it is distinct from JSON `null` (no null values were seen). Values below are for the World row.

| Age query | Breast `cum_risk` | Breast `cum_risk_74` | Lung `cum_risk` | Lung `cum_risk_74` |
| --- | ---: | ---: | ---: | ---: |
| `0_14` | 5.15 | 5.15 | 2.83 | 2.83 |
| `0_15` | 6.06 | 5.15 | 4.18 | 2.83 |
| `0_16` | 6.96 | 5.15 | 5.77 | 2.83 |
| `0_17` | MISSING | 5.15 | MISSING | 2.83 |
| `14_14` | 0.90 | 0.90 | 1.08 | 1.08 |
| `14_15` | 1.84 | 0.90 | 2.45 | 1.08 |
| `14_16` | 2.78 | 0.90 | 4.08 | 1.08 |
| `14_17` | MISSING | 0.90 | MISSING | 1.08 |

For breast incidence, starts 0, 5, 10, 12, 13 and 14 were checked at end index 14; the `cum_risk_74` values correspondingly fall from 5.15 to 5.14, 3.86, 2.55, 1.76 and 0.90. For lung mortality they fall from 2.83 to 2.83, 2.75, 2.34, 1.85 and 1.08. For all 238 returned populations in each test, `cum_risk_74` was exactly equal across end indices 14, 15, 16 and 17 when the start index was held constant: 238/238 for starts 0, 10, 13 and 14. It changes with the start age, so this supports “selected query start through age 74,” not “always from birth through 74.”

`cum_risk` changes as the queried upper endpoint increases through index 16. For breast incidence, 238/238 populations changed between `0_14`, `0_15`, and `0_16`, and 238/238 changed between `14_14`, `14_15`, and `14_16`. For lung mortality the respective changed counts were 235/238 for both starts; the three unchanged records were rounded/sparse values. In both queries, `cum_risk` was missing (the key did not exist) for all 238 rows whenever the query ended at 17 (85+). `cum_risk_74` remained present. This is consistent with an unbounded upper interval preventing a finite cumulative-risk calculation, but that reason is a scientific interpretation; the API itself only establishes the key-missing pattern.

### UI comparison

The Cancer Today table changes the heading with the query. For World female breast incidence, observed UI values are:

| Selected range | UI column / value | Raw API field / value | Match |
| --- | --- | --- | --- |
| 0–74 | Cum. risk / 5.2 | Both fields / 5.15 | Same numeric value; not discriminating |
| 0–79 | Cum. risk / 6.1 | `cum_risk` / 6.06; `cum_risk_74` / 5.15 | `cum_risk` |
| 0–84 | Cum. risk / 7.0 | `cum_risk` / 6.96; `cum_risk_74` / 5.15 | `cum_risk` |
| 70–74 | Cum. risk / 0.90 | Both fields / 0.90 | Same numeric value; not discriminating |
| 70–79 | Cum. risk / 1.8 | `cum_risk` / 1.84 | `cum_risk` |
| 70–84 | Cum. risk / 2.8 | `cum_risk` / 2.78 | `cum_risk` |
| 70–85+ | Cum. risk 74 / 0.90 | `cum_risk_74` / 0.90; `cum_risk` missing | `cum_risk_74` |
| 0–85+ | Cum. risk 74 / 5.2 | `cum_risk_74` / 5.15; `cum_risk` missing | `cum_risk_74` |

Thus the UI “Cum. risk” corresponds to `cum_risk` for closed selected intervals; when the selected range ends in open 85+, `cum_risk` is absent and the UI shows “Cum. risk 74” using `cum_risk_74`. UI rounding accounts for the displayed precision. The page behavior confirms that `cum_risk_74` is not synonymous with the selected full interval risk.

### Formula sanity check and v1 reconstruction rule

For World breast incidence 70–74 (`14_14`), API crude rate and ASR are both 179.93 per 100,000. The standard five-year formula gives `100 × (1 − exp(−5 × 179.93 / 100000)) = 0.8956%`, which rounds to the raw API risk 0.90%. World lung mortality gives 1.0794%, matching API 1.08%. For a reconstructed band, subtract adjacent cumulative counts and populations, recompute its rate, and apply the same formula for closed bands 75–79 and 80–84. This is a mathematical derivation from the standard cumulative-rate method and available API quantities; the direct single-band GCO rate endpoint is empty, so no independently returned 75–79 or 80–84 risk can be compared. A check via differenced cumulative risks (which themselves are rounded to 0.01 percentage point) differed by at most about 0.007 percentage point in the examples tested.

For a single age stratum, the normalized standard-population weight cancels, so its ASR equals its age-specific rate; the API also returned `asr == crude_rate` for all rows in checked single-band queries through 70–74. The derived 85+ crude rate and single-stratum ASR can be calculated from counts/population, but 85+ is open-ended, so no finite five-year width exists for its cumulative risk. A reconstructed high-age row has no equivalent query context for `cum_risk_74`, and the ranking algorithm cannot be reproduced from only the differenced rows. Those unavailable fields are null.

Reconstructed output records are marked in `manifest.json` with `source: "derived_cumulative_difference"`, `derived_from` cumulative age queries, the fields derived, and the unavailable fields. For 75–79 and 80–84, the derived fields are `total`, `total_pop`, `crude_rate`, `asr`, and `cum_risk`. For 85+, the derived fields are `total`, `total_pop`, `crude_rate`, and `asr`; `cum_risk`, `cum_risk_74`, and `rank` are unavailable. No derived value is copied from either cumulative-risk API field.

The 2024 fallback runs only after an empty direct single-band response. Validation requires identical, unique population keys in adjacent cumulative responses, finite nonnegative counts and populations, and nonnegative count differences with a positive population difference. A validation or request error is recorded in `failed`, not `empty`, and does not create a derived table. If all three 75+ bands are requested together and all require reconstruction, they are checked in memory against the 75+ difference (`0_17` minus `0_14`) before any of the three tables is written. This is an arithmetic consistency check of the available cumulative responses, not independent confirmation by a separate upstream 75+ endpoint. Older manifest entries for the known 2024 high-age empty responses are retried; ordinary empty entries remain skipped.
