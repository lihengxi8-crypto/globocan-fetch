# Changelog

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
