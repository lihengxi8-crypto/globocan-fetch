import pytest

from globocan_fetch import cli


def test_populations_filters_mock_metadata(monkeypatch, capsys):
    rows = {156: {"pop_label": "China", "iso3": "CHN", "pop_level": "country"}, 982: {"pop_label": "High HDI", "iso3": None, "pop_level": "hdi"}}
    monkeypatch.setattr(cli, "load_or_fetch", lambda *args, **kwargs: (rows, {}, {}))
    assert cli.main(["populations", "--level", "country"]) == 0
    output = capsys.readouterr().out
    assert "China" in output and "High HDI" not in output and "156" in output
    assert cli.main(["populations", "--level", "hdi"]) == 0
    assert "High HDI" in capsys.readouterr().out
    with pytest.raises(SystemExit, match="Invalid --level"):
        cli.main(["populations", "--level", "invalid"])
