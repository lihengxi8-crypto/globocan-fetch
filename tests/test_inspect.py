import json

from globocan_fetch.cli import main


def test_inspect_reads_manifest_without_network(tmp_path, capsys):
    (tmp_path / "manifest.json").write_text(json.dumps({"software_version": "0.2", "dataset_identity": {"year": 2024, "endpoint_base": "x", "output_format": "csv"}, "parameters": {"metrics": ["incidence"], "sexes": ["female"], "cancers": [20], "ages": [{"label": "0-85+"}]}, "completed": ["x"], "empty": [], "files": {"tables/x.csv": {}}}), encoding="utf-8")
    assert main(["inspect", str(tmp_path)]) == 0
    assert '"files_count": 1' in capsys.readouterr().out


def test_inspect_reports_invalid_json_and_missing_files(tmp_path, capsys):
    (tmp_path / "manifest.json").write_text("{bad", encoding="utf-8")
    try:
        main(["inspect", str(tmp_path)])
    except SystemExit as exc:
        assert "Invalid manifest" in str(exc)
    (tmp_path / "manifest.json").write_text(json.dumps({"files": {"tables/no.csv": {}}}), encoding="utf-8")
    assert main(["inspect", str(tmp_path)]) == 0
    assert "missing_output_files" in capsys.readouterr().out
