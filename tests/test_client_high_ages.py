import pytest

from globocan_fetch.client import GCOClient, GCOError


def test_client_returns_raw_empty_high_age_response_without_reconstruction(monkeypatch):
    client = GCOClient(2024)
    calls = []

    def fake_get(path, params):
        calls.append(params["ages_group"])
        return {"dataset": []}

    monkeypatch.setattr(client, "_get_json", fake_get)
    assert client.rates(0, 2, 20, 15, 15) == {"dataset": []}
    assert calls == ["15_15"]


def test_client_preserves_direct_high_age_rows(monkeypatch):
    client = GCOClient(2024)
    direct = {"dataset": [{"country_code": 900, "cum_risk": 0.5, "cum_risk_74": None}]}
    monkeypatch.setattr(client, "_get_json", lambda path, params: direct)
    assert client.rates(0, 2, 20, 15, 15) == direct


@pytest.mark.parametrize("invalid", [{}, {"dataset": None}, {"dataset": {}}])
def test_client_rejects_missing_or_nonlist_dataset(monkeypatch, invalid):
    client = GCOClient(2024)
    monkeypatch.setattr(client, "_get_json", lambda path, params: invalid)
    with pytest.raises(GCOError, match="list-valued"):
        client.rates(0, 2, 20, 15, 15)
