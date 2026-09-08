from globocan_fetch.schema import FIELD_NAMES, data_dictionary_markdown


def test_generated_dictionary_is_complete_and_bilingual(tmp_path):
    path = tmp_path / "DATA_DICTIONARY.md"
    path.write_text(data_dictionary_markdown(), encoding="utf-8")
    text = path.read_text(encoding="utf-8")
    assert [text.index(f"`{name}`") for name in FIELD_NAMES] == sorted(text.index(f"`{name}`") for name in FIELD_NAMES)
    assert "before age 75" in text and "75 岁前" in text
