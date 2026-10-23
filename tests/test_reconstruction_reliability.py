import csv
import json
import math

import pytest

from globocan_fetch import cli
from globocan_fetch.cli import ReconstructionError, _check_high_age_aggregate, _identity, _reconstruct_single_age_band, main


def row(code=900, total=100, total_pop=1_000_000, **extra):
    return {"country_code": code, "total": total, "total_pop": total_pop, **extra}


def install_client(monkeypatch, responses, calls):
    class FakeClient:
        def __init__(self, year, **kwargs):
            self.base_url = f"https://example.test/{year}"

        def rates(self, metric, sex, cancer, start, end):
            calls.append((start, end))
            value = responses.get((start, end), [])
            if isinstance(value, Exception):
                raise value
            return {"dataset": value}

    monkeypatch.setattr(cli, "GCOClient", FakeClient)
    monkeypatch.setattr(cli, "load_or_fetch", lambda *args, **kwargs: (
        {900: {"pop_label": "World", "pop_level": "world"}},
        {20: {"cancer_label": "Breast", "ICD": "C50"}},
        {"populations_sha256": "p", "cancers_sha256": "c"},
    ))


def download(output, ages, year=2024):
    return main(["download", "--year", str(year), "--metric", "incidence", "--sex", "female",
                 "--cancer", "20", "--age", ages, "--format", "csv", "--output", str(output)])


def manifest(output):
    return json.loads((output / "manifest.json").read_text(encoding="utf-8"))


def cumulative_rows():
    return {(0, 14): [row(total=100, total_pop=1_000_000)],
            (0, 15): [row(total=150, total_pop=1_100_000)],
            (0, 16): [row(total=180, total_pop=1_160_000)],
            (0, 17): [row(total=210, total_pop=1_220_000)]}


def test_direct_high_age_response_is_preferred(monkeypatch, tmp_path):
    calls = []
    direct = row(total=7, total_pop=20_000, cum_risk=0.5, cum_risk_74=0.1, rank=2)
    install_client(monkeypatch, {(15, 15): [direct]}, calls)
    output = tmp_path / "out"
    assert download(output, "15_15") == 0
    assert calls == [(15, 15)]
    with (output / "tables/incidence_female_can20_a15-15.csv").open(newline="") as handle:
        result = next(csv.DictReader(handle))
    assert result["cum_risk"] == "0.5"
    assert result["cum_risk_74"] == "0.1"
    assert result["rank"] == "2"
    assert manifest(output)["files"]["tables/incidence_female_can20_a15-15.csv"]["source"] == "gco_response"


def test_high_age_fallback_only_for_2024(monkeypatch, tmp_path):
    calls = []
    install_client(monkeypatch, cumulative_rows(), calls)
    output = tmp_path / "out"
    assert download(output, "15_15", year=2022) == 0
    assert calls == [(15, 15)]
    assert manifest(output)["empty"] == ["incidence/female/20/15_15"]
    assert not (output / "tables").exists()


@pytest.mark.parametrize("lower,upper,match", [
    ([row(900), row(156)], [row(900)], "population keys differ"),
    ([row(total=120)], [row(total=100)], "negative count"),
    ([row(total_pop=2_000_000)], [row(total_pop=1_000_000)], "nonpositive population"),
    ([row(total=None)], [row(total=120)], "invalid or missing total"),
    ([row(total_pop=float('nan'))], [row(total_pop=2_000_000)], "invalid or missing total_pop"),
    ([row()], [row(total=True)], "invalid or missing total"),
    ([row(), row()], [row()], "duplicate population key"),
])
def test_invalid_reconstruction_inputs_fail(lower, upper, match):
    with pytest.raises(ReconstructionError, match=match):
        _reconstruct_single_age_band(lower, upper, 15)


def test_population_alignment_uses_keys_not_row_position():
    lower = [row(900, 100, 1_000_000), row(156, 40, 500_000)]
    upper = [row(156, 70, 560_000), row(900, 150, 1_100_000)]
    result = _reconstruct_single_age_band(lower, upper, 15)
    assert [(item["country_code"], item["total"]) for item in result] == [(156, 30), (900, 50)]


def test_validation_failure_is_failed_not_empty(monkeypatch, tmp_path):
    calls = []
    responses = {(0, 14): [row(total=100)], (0, 15): [row(total=90)]}
    install_client(monkeypatch, responses, calls)
    output = tmp_path / "out"
    assert download(output, "15_15") == 2
    state = manifest(output)
    assert state["empty"] == []
    assert "incidence/female/20/15_15" in state["failed"]
    assert not (output / "tables/incidence_female_can20_a15-15.csv").exists()


def test_request_failure_is_failed_not_empty(monkeypatch, tmp_path):
    calls = []
    install_client(monkeypatch, {(14, 14): cli.GCOError("network unavailable")}, calls)
    output = tmp_path / "out"
    assert download(output, "14_14") == 2
    assert manifest(output)["empty"] == []
    assert "incidence/female/20/14_14" in manifest(output)["failed"]


def test_all_empty_warns(monkeypatch, tmp_path, capsys):
    calls = []
    install_client(monkeypatch, {}, calls)
    output = tmp_path / "out"
    assert download(output, "14_14") == 0
    assert "all requested datasets were empty" in capsys.readouterr().err


def test_legacy_high_age_empty_retried_but_ordinary_empty_skipped(monkeypatch, tmp_path):
    calls = []
    install_client(monkeypatch, cumulative_rows(), calls)
    output = tmp_path / "out"
    output.mkdir()
    (output / "manifest.json").write_text(json.dumps({
        "schema_version": 3, "dataset_identity": _identity(2024, "https://example.test/2024", "csv"),
        "completed": [], "empty": ["incidence/female/20/14_14", "incidence/female/20/15_15"],
        "files": {}, "metadata": {"populations_sha256": "p", "cancers_sha256": "c"},
    }))
    assert download(output, "14_14,15_15") == 0
    assert (14, 14) not in calls and (15, 15) in calls
    assert manifest(output)["empty"] == ["incidence/female/20/14_14"]
    assert "incidence/female/20/15_15" in manifest(output)["completed"]


def test_aggregate_invariant_accepts_consistent_three_bands():
    cumulative = cumulative_rows()
    bands = {band: _reconstruct_single_age_band(cumulative[(0, band - 1)], cumulative[(0, band)], band)
             for band in (15, 16, 17)}
    _check_high_age_aggregate(bands, cumulative[(0, 14)], cumulative[(0, 17)])
    bands[16][0]["total"] += 1
    with pytest.raises(ReconstructionError, match="aggregate total mismatch"):
        _check_high_age_aggregate(bands, cumulative[(0, 14)], cumulative[(0, 17)])


def test_aggregate_failure_writes_no_derived_csv(monkeypatch, tmp_path):
    calls = []
    responses = cumulative_rows()
    install_client(monkeypatch, responses, calls)
    monkeypatch.setattr(cli, "_check_high_age_aggregate", lambda *args: (_ for _ in ()).throw(ReconstructionError("aggregate mismatch")))
    output = tmp_path / "out"
    assert download(output, "15_15,16_16,17_17") == 2
    assert len(manifest(output)["failed"]) == 3
    assert not (output / "tables").exists()


def test_closed_80_84_risk_and_open_85_plus_rules():
    rows = cumulative_rows()
    age80 = _reconstruct_single_age_band(rows[(0, 15)], rows[(0, 16)], 16)[0]
    assert age80["cum_risk"] == pytest.approx(100 * -math.expm1(-5 * age80["crude_rate"] / 100_000))
    assert age80["asr"] == age80["crude_rate"]
    assert age80["cum_risk_74"] is None and age80["rank"] is None
    age85 = _reconstruct_single_age_band(rows[(0, 16)], rows[(0, 17)], 17)[0]
    assert age85["cum_risk"] is None and age85["cum_risk_74"] is None and age85["rank"] is None


def test_direct_band_survives_other_band_reconstruction_failure(monkeypatch, tmp_path):
    calls = []
    responses = cumulative_rows()
    responses[(15, 15)] = [row(total=7, total_pop=20_000, cum_risk=0.5)]
    responses[(0, 16)] = [row(total=90, total_pop=1_160_000)]
    install_client(monkeypatch, responses, calls)
    output = tmp_path / "out"
    assert download(output, "15_15,16_16,17_17") == 2
    state = manifest(output)
    assert "incidence/female/20/15_15" in state["completed"]
    assert "incidence/female/20/16_16" in state["failed"]
    assert state["files"]["tables/incidence_female_can20_a15-15.csv"]["source"] == "gco_response"


def test_direct_band_survives_other_band_request_failure(monkeypatch, tmp_path):
    calls = []
    responses = cumulative_rows()
    responses[(15, 15)] = [row(total=7, total_pop=20_000, cum_risk=0.5)]
    responses[(16, 16)] = cli.GCOError("temporary request failure")
    install_client(monkeypatch, responses, calls)
    output = tmp_path / "out"
    assert download(output, "15_15,16_16,17_17") == 2
    state = manifest(output)
    assert "incidence/female/20/15_15" in state["completed"]
    assert "incidence/female/20/16_16" in state["failed"]
