# Changelog

## 1.1.0 — 2026-10-23

- Preserve Cancer Today count 95% uncertainty intervals from normal rate responses, with no additional HTTP requests or opt-in flag.
- Upgrade the output schema to v3, appending `ui_lower`, `ui_upper`, `ui_status`, and nullable `point_within_ui`. Flag incomplete and inconsistent upstream intervals without repairing numeric bounds.
- Default to `https://gco-api.iarc.fr/api/globocan/v3/{year}`; add `--api-base` to network commands. Record the actual endpoint in the manifest and dataset identity, with no silent fallback.
- Reject v2 output directories before metadata access or writes. Record interval capabilities and unavailable UI fields in high-age reconstruction provenance.
- Do not infer missing age-specific or Colorectum intervals, copy all-age bounds, or derive UI from cumulative differences. Reconstructed high-age rows explicitly retain unavailable UI bounds.
- Update bilingual documentation and add count-UI, schema compatibility, endpoint, resume, CSV/Parquet and reconstruction regression coverage.

## 1.0.0

### Added
- Reproducible GLOBOCAN Cancer Today downloader with CSV and Parquet output.
- Population and cancer metadata enrichment.
- Manifest-based provenance, file hashes, and resume support.
- `inspect`, `verify`, `cancers`, `populations`, and `download` commands.
- Bilingual English and Chinese data guide and schema-driven data dictionary.

### Data semantics
- Separate `cum_risk` and `cum_risk_74` in the 24-field public schema.
- Document the observed cumulative-risk behavior and its evidentiary limits.

### Reliability
- Validate the GLOBOCAN 2024 high-age compatibility fallback while preferring direct upstream rows.
- Derive 75–79 and 80–84 cumulative risk using the IARC formula; leave 85+ cumulative risk unavailable.
- Record derived-file provenance and track empty and failed tasks separately.

