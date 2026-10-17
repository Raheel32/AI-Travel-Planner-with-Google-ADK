import pytest
from pydantic import ValidationError

from travel_planner.models.trip_models import TripRequest

GOOD = dict(
    origin_city="Karachi", origin_airport="khi", destination_city="Istanbul",
    destination_airport="IST", departure_date="2030-04-10", return_date="2030-04-15",
    travelers=2, budget=1800, currency="usd", interests=["food"],
)


def test_valid_request_is_normalised():
    r = TripRequest(**GOOD)
    assert r.origin_airport == "KHI" and r.currency == "USD" and r.nights == 5


def test_return_before_departure_rejected():
    with pytest.raises(ValidationError):
        TripRequest(**{**GOOD, "return_date": "2030-04-09"})


def test_bad_airport_code_rejected():
    with pytest.raises(ValidationError):
        TripRequest(**{**GOOD, "origin_airport": "Karachi"})
