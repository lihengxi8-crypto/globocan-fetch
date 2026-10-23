import csv
import json

from globocan_fetch.cli import main


def test_help_is_available(capsys):
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    assert "Rate-limited GLOBOCAN" in capsys.readouterr().out


def test_empty_high_age_query_reconstructs_and_records_provenance(tmp_path, monkeypatch, capsys):
    from globocan_fetch import cli

    class FakeClient:
        base_url = "https://example.test/2024"

        def __init__(self, *args, **kwargs):
            pass

        def rates(self, metric, sex, cancer, start, end):
            if (start, end) == (15, 15):
                return {"dataset": []}
            rows = {
                (0, 14): {"country_code": 900, "total": 100, "total_pop": 1_000_000},
                (0, 15): {"country_code": 900, "total": 150, "total_pop": 1_100_000},
            }
            return {"dataset": [rows[(start, end)]]}

    monkeypatch.setattr(cli, "GCOClient", FakeClient)
    monkeypatch.setattr(cli, "load_or_fetch", lambda *a, **k: (
        {900: {"pop_label": "World", "iso3": None, "pop_level": "world"}},
        {20: {"cancer_label": "Breast", "ICD": "C50"}},
        {"populations_sha256": "p", "cancers_sha256": "c"},
    ))
    output = tmp_path / "candidate"
    assert main([
        "download", "--metric", "incidence", "--sex", "female", "--cancer", "20",
        "--age", "15_15", "--format", "csv", "--output", str(output),
    ]) == 0
    capsys.readouterr()

    table = output / "tables" / "incidence_female_can20_a15-15.csv"
    with table.open(encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["total"] == "50"
    assert row["total_pop"] == "100000"
    assert float(row["crude_rate"]) == 50
    assert float(row["asr"]) == 50
    assert float(row["cum_risk"]) > 0
    assert row["cum_risk_74"] == ""
    assert row["rank"] == ""
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    provenance = manifest["files"]["tables/incidence_female_can20_a15-15.csv"]
    assert provenance["source"] == "derived_cumulative_difference"
    assert provenance["direct_query"] == "15_15"
    assert provenance["direct_query_result"] == "empty"
    assert provenance["derived_from"] == ["0_14", "0_15"]
    assert provenance["derived_fields"] == ["total", "total_pop", "crude_rate", "asr", "cum_risk"]
    assert provenance["unavailable_fields"] == ["cum_risk_74", "rank", "ui_lower", "ui_upper", "point_within_ui"]
