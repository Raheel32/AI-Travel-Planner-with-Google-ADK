"""Tools that create and read the shared trip request (stored in session state)."""
from __future__ import annotations

import json
from datetime import date

from google.adk.tools import ToolContext
from pydantic import ValidationError

from ..models.trip_models import TripRequest

STATE_KEY = "trip_request"


def save_trip_request(
    origin_city: str,
    origin_airport: str,
    destination_city: str,
    destination_airport: str,
    departure_date: str,
    return_date: str,
    travelers: int,
    budget: float,
    currency: str,
    interests: list[str],
    tool_context: ToolContext,
) -> dict:
    """Validate and save the trip request so the specialist agents can use it.

    Call this ONLY once you know every field.

    Args:
        origin_city: City the traveler departs from, e.g. "Karachi".
        origin_airport: 3-letter IATA code of the departure airport, e.g. "KHI".
        destination_city: Destination city, e.g. "Istanbul".
        destination_airport: 3-letter IATA code of the arrival airport, e.g. "IST".
        departure_date: Departure date as YYYY-MM-DD.
        return_date: Return date as YYYY-MM-DD.
        travelers: Number of travelers (1-9).
        budget: Total budget for the whole trip, all travelers combined.
        currency: 3-letter currency code, e.g. "USD".
        interests: Interests such as ["history", "food"]. May be empty.

    Returns:
        A dict with status "saved" or status "error" and a message to fix.
    """
    try:
        req = TripRequest(
            origin_city=origin_city, origin_airport=origin_airport,
            destination_city=destination_city, destination_airport=destination_airport,
            departure_date=departure_date, return_date=return_date,
            travelers=travelers, budget=budget, currency=currency, interests=interests,
        )
    except ValidationError as exc:
        problems = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
        return {"status": "error", "message": f"Invalid trip request - {problems}"}

    if req.departure_date < date.today():
        return {"status": "error", "message": "departure_date is in the past. Ask the user for a future date."}

    tool_context.state[STATE_KEY] = req.model_dump_json()
    return {"status": "saved", "nights": req.nights, "trip_request": json.loads(req.model_dump_json())}


def load_trip_request(tool_context: ToolContext) -> TripRequest | None:
    """Read the saved trip request back out of session state (None if missing)."""
    raw = tool_context.state.get(STATE_KEY)
    if not raw:
        return None
    return TripRequest.model_validate_json(raw)
