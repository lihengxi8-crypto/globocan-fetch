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

