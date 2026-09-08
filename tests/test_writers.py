from globocan_fetch.writers import sha256, write_rows


def test_csv_is_atomically_written(tmp_path):
    target = tmp_path / "out.csv"
    write_rows([{"country_code": 900, "pop_label": "World", "total": 1}], target, "csv")
    assert target.exists()
    assert not (tmp_path / "out.csv.partial").exists()
    assert len(sha256(target)) == 64
    assert "country_code" in target.read_text(encoding="utf-8")

