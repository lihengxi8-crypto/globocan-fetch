# Release checklist

- [ ] Replace the placeholder repository URL in `CITATION.cff`.
- [ ] Add maintainers to `pyproject.toml` and a `CODEOWNERS` file if needed.
- [ ] Run `python -m pytest` without network access.
- [ ] Run `globocan-fetch verify --year 2024` and record the result in the release notes.
- [ ] Re-read current GCO/IARC terms of use. Do not publish downloaded GLOBOCAN data unless redistribution is explicitly permitted.
- [ ] Keep generated `data/`, metadata caches, logs and manifests out of commits.
- [ ] Tag a version and add a short changelog.

