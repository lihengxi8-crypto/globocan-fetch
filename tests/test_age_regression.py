import csv
import json

from globocan_fetch import cli
from globocan_fetch.client import GCOError


class FakeClient:
    responses = {}

    def __init__(self, year, **kwargs):
        self.base_url = f"https://example.invalid/{year}"

    def rates(self, metric, sex, cancer, age_start, age_end):
        result = self.responses[(age_start, age_end)]
        if isinstance(result, Exception):
            raise result
        return {"dataset": result}


def setup_fake(monkeypatch):
    monkeypatch.setattr(cli, "GCOClient", FakeClient)
    monkeypatch.setattr(cli, "load_or_fetch", lambda client, cache_dir, refresh=False: (
        {900: {"pop_label": "World", "pop_level": "world"}},
        {20: {"cancer_label": "Breast", "ICD": "C50"}},
        {"populations_sha256": "pop", "cancers_sha256": "cancer"},
    ))


def download(output, ages):
    return cli.main(["download", "--metric", "incidence", "--sex", "female",
                     "--cancer", "20", "--age", ages,
                     "--format", "csv", "--output", str(output)])


def test_direct_high_ages_reach_writer_and_completed_path(monkeypatch, tmp_path):
    setup_fake(monkeypatch)
    FakeClient.responses = {(age, age): [{"country_code": 900, "total": age}] for age in (15, 16, 17)}
    assert download(tmp_path, "15_15,16_16,17_17") == 0
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["completed"] == [f"incidence/female/20/{age}_{age}" for age in (15, 16, 17)]
    assert manifest["empty"] == [] and manifest["failed"] == {}
    for age in (15, 16, 17):
        with (tmp_path / "tables" / f"incidence_female_can20_a{age}-{age}.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == 1 and rows[0]["total"] == str(age)


def test_ordinary_empty_and_failed_tasks_are_distinct(monkeypatch, tmp_path):
    setup_fake(monkeypatch)
    FakeClient.responses = {(13, 13): [], (14, 14): GCOError("HTTP 503")}
    assert download(tmp_path, "13_13,14_14") == 2
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["empty"] == ["incidence/female/20/13_13"]
    assert manifest["failed"] == {"incidence/female/20/14_14": "HTTP 503"}


def test_all_ordinary_empty_tasks_warn(monkeypatch, tmp_path, capsys):
    setup_fake(monkeypatch)
    FakeClient.responses = {(13, 13): [], (14, 14): []}
    assert download(tmp_path, "13_13,14_14") == 0
    assert "all requested datasets were empty" in capsys.readouterr().err


def test_failed_task_retried_but_ordinary_empty_skipped(monkeypatch, tmp_path):
    setup_fake(monkeypatch)
    FakeClient.responses = {(13, 13): [], (14, 14): GCOError("temporary")}
    assert download(tmp_path, "13_13,14_14") == 2
    FakeClient.responses = {(13, 13): GCOError("should not be retried"),
                            (14, 14): [{"country_code": 900, "total": 1}]}
    assert download(tmp_path, "13_13,14_14") == 0
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["failed"] == {}
    assert manifest["empty"] == ["incidence/female/20/13_13"]
    assert manifest["completed"] == ["incidence/female/20/14_14"]
