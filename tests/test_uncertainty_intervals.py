import copy
import csv
import json
from pathlib import Path

import pytest

from globocan_fetch import cli
from globocan_fetch.cli import _parse_ui, _rows
from globocan_fetch.client import GCOClient, GCOError
from globocan_fetch.schema import SCHEMA_VERSION, UI_METADATA
from globocan_fetch.writers import write_rows


NO_UI = {"ui_lower": None, "ui_upper": None, "ui_status": "not_provided", "point_within_ui": None}
CANCER = {"code": 20, "cancer_label": "Breast", "ICD": "C50"}
AGE = {"start": 0, "end": 17, "label": "0-85+"}


@pytest.mark.parametrize("source,expected", [
    ({"total": 375808, "ui": {"low": 373555, "high": 378075}},
     {"ui_lower": 373555, "ui_upper": 378075, "ui_status": "complete", "point_within_ui": True}),
    ({"total": 59957}, NO_UI),
    ({"total": 0, "ui": {"low": 0}},
     {"ui_lower": 0, "ui_upper": None, "ui_status": "incomplete", "point_within_ui": None}),
    ({"total": 10, "ui": {"low": 0, "high": 0}},
     {"ui_lower": 0, "ui_upper": 0, "ui_status": "point_outside_interval", "point_within_ui": False}),
    ({"total": 3, "ui": {"low": 4, "high": 5}},
     {"ui_lower": 4, "ui_upper": 5, "ui_status": "point_outside_interval", "point_within_ui": False}),
    ({"total": 3, "ui": {"low": 5, "high": 1}},
     {"ui_lower": 5, "ui_upper": 1, "ui_status": "point_outside_interval", "point_within_ui": False}),
    ({"total": 0, "ui": {"low": 0, "high": 0}},
     {"ui_lower": 0, "ui_upper": 0, "ui_status": "complete", "point_within_ui": True}),
])
def test_parse_ui_preserves_values_and_flags_quality(source, expected):
    original = copy.deepcopy(source)
    assert _parse_ui(source) == expected
    assert source == original


@pytest.mark.parametrize("unavailable", [None, "NA", "123", True, float("nan"), float("inf"), float("-inf")])
def test_unavailable_bound_is_nullable_not_false(unavailable):
    result = _parse_ui({"total": 10, "ui": {"low": 0, "high": unavailable}})
    assert result == {"ui_lower": 0, "ui_upper": None, "ui_status": "incomplete", "point_within_ui": None}


@pytest.mark.parametrize("ui", [None, {}, [], "NA"])
def test_present_but_unusable_ui_is_incomplete(ui):
    assert _parse_ui({"total": 10, "ui": ui}) == {**NO_UI, "ui_status": "incomplete"}


def test_missing_point_cannot_be_flagged_inside_or_outside():
    assert _parse_ui({"ui": {"low": 1, "high": 3}}) == {
        "ui_lower": 1, "ui_upper": 3, "ui_status": "incomplete", "point_within_ui": None,
    }


@pytest.mark.parametrize("band", [15, 16, 17])
def test_reconstructed_bands_never_subtract_or_copy_cumulative_ui(band):
    previous = [{"country_code": 900, "total": 100, "total_pop": 1000, "ui": {"low": 90, "high": 110}}]
    current = [{"country_code": 900, "total": 120, "total_pop": 2000, "ui": {"low": 100, "high": 140}}]
    derived = cli._reconstruct_single_age_band(previous, current, band)
    normalized = _rows(derived, {}, CANCER, "incidence", "female", {"start": band, "end": band, "label": "high-age"})[0]
    assert {key: normalized[key] for key in NO_UI} == NO_UI
    assert normalized["total"] == 20


class Response:
    status_code = 200
    headers = {}

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return copy.deepcopy(self.payload)


class Session:
    def __init__(self, payload):
        self.headers = {}
        self.calls = []
        self.payload = payload

    def get(self, url, params, timeout):
        self.calls.append((url, params))
        return Response(self.payload)


def metadata(*args, **kwargs):
    return ({156: {"pop_label": "China", "iso3": "CHN", "pop_level": "country"}},
            {20: {"cancer_label": "Breast", "ICD": "C50"}},
            {"populations_sha256": "p", "cancers_sha256": "c"})


@pytest.mark.parametrize("api_base", [None, "https://example.test/custom/2024/"])
def test_endpoint_manifest_and_resume_with_no_extra_ui_request(tmp_path, monkeypatch, api_base):
    session = Session({"dataset": [{"country_code": 156, "total": 375808, "ui": {"low": 373555, "high": 378075}}]})
    monkeypatch.setattr("globocan_fetch.client.requests.Session", lambda: session)
    monkeypatch.setattr(cli, "load_or_fetch", metadata)
    args = ["download", "--sex", "female", "--cancer", "20", "--format", "csv", "--output", str(tmp_path)]
    if api_base:
        args += ["--api-base", api_base]
    assert cli.main(args) == 0
    expected_base = (api_base or "https://gco-api.iarc.fr/api/globocan/v3/2024").rstrip("/")
    assert session.calls == [(expected_base + "/data/rate/0/2/all/20/", {"ages_group": "0_17"})]
    state = json.loads((tmp_path / "manifest.json").read_text())
    assert state["endpoint_base"] == state["dataset_identity"]["endpoint_base"] == expected_base
    assert state["schema_version"] == state["dataset_identity"]["schema_version"] == SCHEMA_VERSION == 3
    assert state["uncertainty_intervals"] == UI_METADATA
    table = tmp_path / "tables/incidence_female_can20_a0-17.csv"
    with table.open(newline="") as handle:
        row = next(csv.DictReader(handle))
    assert (row["ui_lower"], row["ui_upper"], row["ui_status"], row["point_within_ui"]) == ("373555", "378075", "complete", "True")
    content = table.read_bytes()
    assert cli.main(args) == 0
    assert len(session.calls) == 1 and table.read_bytes() == content
    # Endpoint identity prevents mixing even when output format/year remain the same.
    with pytest.raises(SystemExit, match="different dataset configuration"):
        cli.main(args + ["--api-base", "https://different.test/2024"])
    assert len(session.calls) == 1


@pytest.mark.parametrize("with_identity", [False, True])
def test_v2_directory_rejected_before_network_or_any_output_write(tmp_path, monkeypatch, with_identity):
    old = {"schema_version": 2, "completed": [], "empty": [], "files": {}}
    if with_identity:
        old["dataset_identity"] = {**cli._identity(2024, "https://gco-api.iarc.fr/api/globocan/v3/2024", "csv"), "schema_version": 2}
    target = tmp_path / "manifest.json"
    target.write_text(json.dumps(old))
    before = target.read_bytes()
    monkeypatch.setattr(cli, "load_or_fetch", lambda *a, **k: pytest.fail("v2 output must be rejected before metadata access"))
    with pytest.raises(SystemExit, match="different schema version"):
        cli.main(["download", "--format", "csv", "--output", str(tmp_path)])
    assert target.read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["manifest.json"]


def test_default_endpoint_and_no_silent_fallback():
    session = Session({})
    client = GCOClient(2024, session=session, retries=1, requests_per_second=0)
    assert client.base_url == "https://gco-api.iarc.fr/api/globocan/v3/2024"
    with pytest.raises(GCOError, match="no list-valued"):
        client.rates(0, 2, 20, 0, 17)
    assert len(session.calls) == 1
    assert session.calls[0][0].startswith(client.base_url)


@pytest.mark.parametrize("fmt", ["csv", "parquet"])
def test_writers_preserve_nullable_ui_and_anomalies(tmp_path, fmt):
    if fmt == "parquet":
        pytest.importorskip("pandas")
        pytest.importorskip("pyarrow")
    rows = _rows([
        {"country_code": 156, "total": 10, "ui": {"low": 0, "high": 0}},
        {"country_code": 840, "total": 59957},
        {"country_code": 900, "total": 0, "ui": {"low": 0}},
    ], {}, CANCER, "incidence", "female", AGE)
    path = write_rows(rows, tmp_path / f"ui.{fmt}", fmt)
    if fmt == "csv":
        with path.open(newline="") as handle:
            result = list(csv.DictReader(handle))
        assert result[0]["ui_lower"] == result[0]["ui_upper"] == "0"
        assert result[0]["point_within_ui"] == "False"
        assert result[1]["ui_lower"] == result[1]["ui_upper"] == result[1]["point_within_ui"] == ""
        assert result[2]["ui_lower"] == "0" and result[2]["ui_upper"] == ""
    else:
        pd = pytest.importorskip("pandas")
        pytest.importorskip("pyarrow")
        result = pd.read_parquet(path)
        assert result.loc[0, "ui_lower"] == result.loc[0, "ui_upper"] == 0
        assert not result.loc[0, "point_within_ui"]
        assert result.loc[1, ["ui_lower", "ui_upper", "point_within_ui"]].isna().all()
        assert result.loc[2, "ui_lower"] == 0 and pd.isna(result.loc[2, "ui_upper"])


def test_normalization_keeps_non_ui_numeric_fields_unchanged():
    source = {"country_code": 156, "total": 375808, "total_pop": 700000000, "asr": 33.17,
              "crude_rate": 53.69, "cum_risk": 4.1, "cum_risk_74": 3.9, "rank": 3,
              "ui": {"low": 373555, "high": 378075}}
    result = _rows([source], {}, CANCER, "incidence", "female", AGE)[0]
    for name in ("total", "total_pop", "asr", "crude_rate", "cum_risk", "cum_risk_74", "rank"):
        assert result[name] == source[name]


@pytest.mark.parametrize("ages", ["15_15", "15_15,16_16,17_17"])
def test_real_client_reconstruction_provenance_discards_any_ui(tmp_path, monkeypatch, ages):
    def get_json(self, path, params=None):
        start, end = map(int, params["ages_group"].split("_"))
        if start != 0:
            return {"dataset": []}
        return {"dataset": [{"country_code": 156, "sex": 2, "type": 0, "cancer_code": 20,
                             "total": 100 + end * 10, "total_pop": 100000 + end * 1000,
                             "ui": {"low": 0, "high": 9999}}]}
    monkeypatch.setattr(GCOClient, "_get_json", get_json)
    monkeypatch.setattr(cli, "load_or_fetch", metadata)
    assert cli.main(["download", "--sex", "female", "--cancer", "20", "--age", ages,
                     "--format", "csv", "--output", str(tmp_path)]) == 0
    state = json.loads((tmp_path / "manifest.json").read_text())
    for name, info in state["files"].items():
        assert info["source"] == "derived_cumulative_difference"
        assert {"ui_lower", "ui_upper", "point_within_ui"} <= set(info["unavailable_fields"])
        with (tmp_path / name).open(newline="") as handle:
            r = next(csv.DictReader(handle))
        assert r["ui_lower"] == r["ui_upper"] == r["point_within_ui"] == ""
        assert r["ui_status"] == "not_provided"


@pytest.mark.parametrize("code,age_range,point", [(20, (10, 10), 59957), (41, (0, 17), 100)])
def test_age_restricted_and_colorectum_rows_save_null_without_extra_requests(tmp_path, monkeypatch, code, age_range, point):
    session = Session({"dataset": [{"country_code": 156, "cancer_code": code, "total": point}]})
    monkeypatch.setattr("globocan_fetch.client.requests.Session", lambda: session)
    monkeypatch.setattr(cli, "load_or_fetch", lambda *a, **k: (
        {}, {code: {"cancer_label": "Example", "ICD": ""}},
        {"populations_sha256": "p", "cancers_sha256": "c"},
    ))
    start, end = age_range
    assert cli.main(["download", "--sex", "female", "--cancer", str(code), "--age", f"{start}_{end}",
                     "--format", "csv", "--output", str(tmp_path)]) == 0
    assert len(session.calls) == 1
    path = next((tmp_path / "tables").glob("*.csv"))
    with path.open(newline="") as f:
        row = next(csv.DictReader(f))
    assert row["total"] == str(point)
    assert row["ui_lower"] == row["ui_upper"] == row["point_within_ui"] == ""
    assert row["ui_status"] == "not_provided"
