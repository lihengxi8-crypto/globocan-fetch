from pathlib import Path

from globocan_fetch.schema import FIELD_NAMES
import re


ROOT = Path(__file__).parents[1]


def test_readmes_name_every_schema_field():
    for name in ("README.md", "README.zh-CN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert all(f"`{field}`" in text for field in FIELD_NAMES), name


def test_readme_section_markers_are_bilingual_and_ordered():
    markers = []
    for name in ("README.md", "README.zh-CN.md"):
        markers.append(re.findall(r"<!-- section: ([a-z0-9-]+) -->", (ROOT / name).read_text(encoding="utf-8")))
    assert markers[0] == markers[1]
    assert len(markers[0]) == 16


def test_readme_concept_markers_match():
    concepts = [re.findall(r"<!-- concept: ([a-z0-9-]+) -->", (ROOT / name).read_text(encoding="utf-8")) for name in ("README.md", "README.zh-CN.md")]
    assert concepts[0] == concepts[1] == ["cum-risk-0-74", "asr-not-additive", "country-filter", "cancer-code-not-icd"]
