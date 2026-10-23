import json

import pytest

from globocan_fetch.cli import _ensure_identity, _identity, _reconstruct_single_age_band, _rows
from globocan_fetch.schema import FIELD_NAMES, data_dictionary_markdown
from globocan_fetch.writers import FIELD_NAMES as WRITER_FIELDS


def test_writer_uses_the_public_schema():
    assert WRITER_FIELDS == FIELD_NAMES
    assert FIELD_NAMES == [
        "country_code", "pop_label", "iso3", "pop_level", "grouping", "area_label", "who_region",
        "hdi_label", "income_label", "sex", "metric", "cancer_code", "cancer_label", "ICD",
        "age_start_idx", "age_end_idx", "age_label", "total", "total_pop", "asr", "crude_rate",
        "cum_risk", "cum_risk_74", "rank", "ui_lower", "ui_upper", "ui_status", "point_within_ui",
    ]


def test_dictionary_covers_every_field():
    text = data_dictionary_markdown()
    assert all(f"`{name}`" in text for name in FIELD_NAMES)


def test_cumulative_risk_fields_are_separate_and_missing_values_stay_null():
    cancer = {"code": 20, "cancer_label": "Breast", "ICD": "C50"}
    age = {"start": 0, "end": 14, "label": "0-74"}
    rows = _rows([
        {"country_code": 900, "cum_risk": 5.15, "cum_risk_74": 4.99},
        {"country_code": 156, "cum_risk_74": None},
        {"country_code": 840, "cum_risk": 9.2},
    ], {}, cancer, "incidence", "female", age)
    assert rows[0]["cum_risk"] == 5.15
    assert rows[0]["cum_risk_74"] == 4.99
    assert rows[1]["cum_risk"] is None
    assert rows[1]["cum_risk_74"] is None
    assert rows[2]["cum_risk"] == 9.2
    assert rows[2]["cum_risk_74"] is None


def test_reconstruct_closed_five_year_band_from_cumulative_counts():
    previous = [{"country_code": 900, "total": 100, "total_pop": 1_000_000}]
    current = [{"country_code": 900, "total": 150, "total_pop": 1_100_000}]
    row = _reconstruct_single_age_band(previous, current, 15)[0]
    assert row["total"] == 50
    assert row["total_pop"] == 100_000
    assert row["crude_rate"] == 50
    assert row["asr"] == 50
    assert row["cum_risk"] == pytest.approx(100 * (1 - __import__("math").exp(-0.0025)))
    assert row["cum_risk_74"] is None
    assert row["rank"] is None


def test_reconstructed_open_ended_age_band_has_no_cumulative_risk():
    row = _reconstruct_single_age_band(
        [{"country_code": 900, "total": 100, "total_pop": 1_000_000}],
        [{"country_code": 900, "total": 120, "total_pop": 1_100_000}],
        17,
    )[0]
    assert row["cum_risk"] is None
    assert row["cum_risk_74"] is None


def test_manifest_identity_rejects_a_different_year_or_format():
    identity = _identity(2024, "https://example/2024", "parquet")
    _ensure_identity({"dataset_identity": identity}, identity)
    with pytest.raises(SystemExit, match="different dataset configuration"):
        _ensure_identity({"dataset_identity": identity}, _identity(2022, "https://example/2022", "parquet"))
    with pytest.raises(SystemExit, match="different dataset configuration"):
        _ensure_identity({"dataset_identity": identity}, _identity(2024, "https://example/2024", "csv"))
    with pytest.raises(SystemExit, match="legacy manifest"):
        _ensure_identity({"completed": ["old/task"]}, identity)
