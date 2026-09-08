import json

import pytest

from globocan_fetch.cli import _ensure_identity, _identity
from globocan_fetch.schema import FIELD_NAMES, data_dictionary_markdown
from globocan_fetch.writers import FIELD_NAMES as WRITER_FIELDS


def test_writer_uses_the_public_schema():
    assert WRITER_FIELDS == FIELD_NAMES


def test_dictionary_covers_every_field():
    text = data_dictionary_markdown()
    assert all(f"`{name}`" in text for name in FIELD_NAMES)


def test_manifest_identity_rejects_a_different_year_or_format():
    identity = _identity(2024, "https://example/2024", "parquet")
    _ensure_identity({"dataset_identity": identity}, identity)
    with pytest.raises(SystemExit, match="different dataset configuration"):
        _ensure_identity({"dataset_identity": identity}, _identity(2022, "https://example/2022", "parquet"))
    with pytest.raises(SystemExit, match="different dataset configuration"):
        _ensure_identity({"dataset_identity": identity}, _identity(2024, "https://example/2024", "csv"))
    with pytest.raises(SystemExit, match="legacy manifest"):
        _ensure_identity({"completed": ["old/task"]}, identity)
