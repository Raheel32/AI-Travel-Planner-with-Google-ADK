import asyncio

from travel_planner import config
from travel_planner.models.trip_models import TripRequest
from travel_planner.services import providers

REQ = TripRequest(
    origin_city="Karachi", origin_airport="KHI", destination_city="Istanbul",
    destination_airport="IST", departure_date="2030-04-10", return_date="2030-04-15",
    travelers=2, budget=1800, currency="USD", interests=[],
)


def test_mock_flights_sorted_and_labelled(monkeypatch):
    monkeypatch.setattr(config, "DATA_PROVIDER", "mock")
    res = asyncio.run(providers.search_flights(REQ))
    prices = [o.price for o in res.options]
    assert prices == sorted(prices)
    assert res.cheapest_price_per_traveler == prices[0]
    assert "MOCK" in res.note


def test_mock_hotels_total_matches_nights(monkeypatch):
    monkeypatch.setattr(config, "DATA_PROVIDER", "mock")
    res = asyncio.run(providers.search_hotels(REQ))
    first = res.options[0]
    assert first.total_rate == round(first.rate_per_night * REQ.nights, 2)


def test_serpapi_without_key_raises_clear_error(monkeypatch):
    monkeypatch.setattr(config, "DATA_PROVIDER", "serpapi")
    monkeypatch.setattr(config, "SERPAPI_KEY", "")
    try:
        asyncio.run(providers.search_flights(REQ))
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "SERPAPI_API_KEY" in str(exc)


def test_parse_serpapi_flights_shape():
    sample = {"best_flights": [{"price": 420, "total_duration": 600, "flights": [
        {"airline": "A", "flight_number": "A 1", "departure_airport": {"time": "2030-04-10 01:00"},
         "arrival_airport": {"time": "2030-04-10 07:00"}}]}], "other_flights": []}
    opts = providers._parse_serp_flights(sample, "USD")
    assert opts[0].price == 420 and opts[0].stops == 0 and opts[0].is_best


def test_parse_serpapi_hotels_skips_missing_rates():
    sample = {"properties": [{"name": "X"}, {"name": "Y", "rate_per_night": {"extracted_lowest": 80}}]}
    opts = providers._parse_serp_hotels(sample, "USD")
    assert [o.name for o in opts] == ["Y"]
