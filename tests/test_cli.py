from globocan_fetch.cli import main


def test_help_is_available(capsys):
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    assert "Rate-limited GLOBOCAN" in capsys.readouterr().out
