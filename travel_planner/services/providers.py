"""Data providers: the ONLY place that knows where flight/hotel data comes from.

Tools call `search_flights()` / `search_hotels()` here. Which backend answers
is chosen by TRAVEL_DATA_PROVIDER ("mock" or "serpapi"). To add Duffel or
LiteAPI later, write one new function and add one `if` branch - no agent changes.
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone

import httpx

from .. import config
from ..models.trip_models import (
    FlightOption,
    FlightSearchResult,
    HotelOption,
    HotelSearchResult,
    TripRequest,
)

SERPAPI_URL = "https://serpapi.com/search.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _seed(*parts: str) -> int:
    """Deterministic number from text, so mock data is stable between runs."""
    return int(hashlib.sha256("|".join(parts).encode()).hexdigest()[:8], 16)


# --------------------------------------------------------------------------
# SerpApi client with on-disk cache
# --------------------------------------------------------------------------
async def _serpapi_get(params: dict) -> dict:
    if not config.SERPAPI_KEY:
        raise RuntimeError(
            "SERPAPI_API_KEY is not set. Add it to travel_planner/.env or set "
            "TRAVEL_DATA_PROVIDER=mock."
        )
    # The cache key excludes the API key so it is never written to disk.
    key = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:24]
    config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = config.CACHE_DIR / f"serpapi_{key}.json"
    if path.exists() and time.time() - path.stat().st_mtime < config.CACHE_TTL_HOURS * 3600:
        return json.loads(path.read_text(encoding="utf-8"))

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(SERPAPI_URL, params={**params, "api_key": config.SERPAPI_KEY})
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        # Don't re-raise the original: its message contains the URL (with the key).
        raise RuntimeError(f"SerpApi request failed (HTTP {exc.response.status_code}).") from None
    except httpx.HTTPError as exc:
        raise RuntimeError(f"SerpApi request failed ({type(exc).__name__}).") from None

    if data.get("error"):
        raise RuntimeError(f"SerpApi error: {data['error']}")
    path.write_text(json.dumps(data), encoding="utf-8")
    return data


# --------------------------------------------------------------------------
# Flights
# --------------------------------------------------------------------------
def _mock_flights(req: TripRequest) -> FlightSearchResult:
    s = _seed(req.origin_airport, req.destination_airport, str(req.departure_date))
    base = 280 + s % 420
    d = str(req.departure_date)
    options = [
        FlightOption(airlines=["Mock Air"], flight_numbers=["MA 101"], price=float(base),
                     currency=req.currency, stops=1, total_duration_minutes=640 + s % 120,
                     departure_time=f"{d} 02:10", arrival_time=f"{d} 13:05", is_best=True),
        FlightOption(airlines=["Demo Airways"], flight_numbers=["DA 450"], price=float(base + 95),
                     currency=req.currency, stops=0, total_duration_minutes=410 + s % 60,
                     departure_time=f"{d} 09:30", arrival_time=f"{d} 16:20"),
        FlightOption(airlines=["Sample Jet", "Mock Air"], flight_numbers=["SJ 77", "MA 330"],
                     price=float(base - 60), currency=req.currency, stops=2,
                     total_duration_minutes=900 + s % 150,
                     departure_time=f"{d} 21:45", arrival_time=f"{d} 14:30"),
    ]
    options.sort(key=lambda o: o.price)
    return FlightSearchResult(
        provider="mock", retrieved_at=_now(), currency=req.currency, options=options,
        cheapest_price_per_traveler=options[0].price,
        note="MOCK DATA - not real flights or prices.",
    )


def _parse_serp_flights(data: dict, currency: str) -> list[FlightOption]:
    options: list[FlightOption] = []
    for group in ("best_flights", "other_flights"):
        for item in data.get(group, []):
            segs = item.get("flights") or []
            if not segs or item.get("price") is None:
                continue
            airlines = list(dict.fromkeys(s.get("airline", "Unknown") for s in segs))
            options.append(FlightOption(
                airlines=airlines,
                flight_numbers=[s["flight_number"] for s in segs if s.get("flight_number")],
                price=float(item["price"]),
                currency=currency,
                stops=max(len(segs) - 1, 0),
                total_duration_minutes=item.get("total_duration"),
                departure_time=(segs[0].get("departure_airport") or {}).get("time"),
                arrival_time=(segs[-1].get("arrival_airport") or {}).get("time"),
                is_best=group == "best_flights",
            ))
    options.sort(key=lambda o: o.price)
    return options[:6]


async def search_flights(req: TripRequest) -> FlightSearchResult:
    if config.DATA_PROVIDER == "mock":
        return _mock_flights(req)
    if config.DATA_PROVIDER == "serpapi":
        data = await _serpapi_get({
            "engine": "google_flights",
            "departure_id": req.origin_airport,
            "arrival_id": req.destination_airport,
            "outbound_date": req.departure_date.isoformat(),
            "return_date": req.return_date.isoformat(),
            "type": "1",  # 1 = round trip
            "adults": req.travelers,
            "currency": req.currency,
            "hl": "en",
        })
        options = _parse_serp_flights(data, req.currency)
        return FlightSearchResult(
            provider="serpapi (Google Flights)", retrieved_at=_now(), currency=req.currency,
            options=options,
            cheapest_price_per_traveler=options[0].price if options else None,
            note=(
                "Round-trip price shown per traveler (assumed - verify on the booking page). "
                "Times shown are for the OUTBOUND leg only. Prices can change."
                if options else "No flight offers returned for these dates/airports."
            ),
        )
    raise RuntimeError(f"Unknown TRAVEL_DATA_PROVIDER '{config.DATA_PROVIDER}'. Use 'mock' or 'serpapi'.")


# --------------------------------------------------------------------------
# Hotels
# --------------------------------------------------------------------------
def _mock_hotels(req: TripRequest) -> HotelSearchResult:
    s = _seed(req.destination_airport, str(req.departure_date))
    base = 45 + s % 40
    cur = req.currency
    options = [
        HotelOption(name="Mock Budget Inn", rate_per_night=float(base), currency=cur, rating=3.9,
                    hotel_class=2, amenities=["Free Wi-Fi", "Breakfast"]),
        HotelOption(name="Demo Central Hotel", rate_per_night=float(base + 40), currency=cur,
                    rating=4.3, hotel_class=3, amenities=["Free Wi-Fi", "Air-conditioning", "Gym"]),
        HotelOption(name="Sample Grand Palace", rate_per_night=float(base + 130), currency=cur,
                    rating=4.6, hotel_class=5, amenities=["Pool", "Spa", "Breakfast", "Free Wi-Fi"]),
    ]
    for o in options:
        o.total_rate = round(o.rate_per_night * req.nights, 2)
    return HotelSearchResult(
        provider="mock", retrieved_at=_now(), currency=cur, options=options,
        cheapest_rate_per_night=options[0].rate_per_night,
        note="MOCK DATA - not real hotels or prices.",
    )


def _parse_serp_hotels(data: dict, currency: str) -> list[HotelOption]:
    options: list[HotelOption] = []
    for p in data.get("properties", []):
        rate = (p.get("rate_per_night") or {}).get("extracted_lowest")
        if rate is None:
            continue
        gps = p.get("gps_coordinates") or {}
        options.append(HotelOption(
            name=p.get("name", "Unknown hotel"),
            rate_per_night=float(rate),
            total_rate=(p.get("total_rate") or {}).get("extracted_lowest"),
            currency=currency,
            rating=p.get("overall_rating"),
            hotel_class=p.get("extracted_hotel_class"),
            latitude=gps.get("latitude"),
            longitude=gps.get("longitude"),
            amenities=(p.get("amenities") or [])[:6],
            link=p.get("link"),
        ))
    options.sort(key=lambda o: o.rate_per_night)
    return options[:6]


async def search_hotels(req: TripRequest) -> HotelSearchResult:
    if config.DATA_PROVIDER == "mock":
        return _mock_hotels(req)
    if config.DATA_PROVIDER == "serpapi":
        data = await _serpapi_get({
            "engine": "google_hotels",
            "q": f"Hotels in {req.destination_city}",
            "check_in_date": req.departure_date.isoformat(),
            "check_out_date": req.return_date.isoformat(),
            "adults": req.travelers,
            "currency": req.currency,
            "hl": "en",
        })
        options = _parse_serp_hotels(data, req.currency)
        return HotelSearchResult(
            provider="serpapi (Google Hotels)", retrieved_at=_now(), currency=req.currency,
            options=options,
            cheapest_rate_per_night=options[0].rate_per_night if options else None,
            note=(
                "Rates are per night for the search's room configuration; availability "
                "and price must be confirmed with the hotel/booking site."
                if options else "No hotel offers returned for these dates."
            ),
        )
    raise RuntimeError(f"Unknown TRAVEL_DATA_PROVIDER '{config.DATA_PROVIDER}'. Use 'mock' or 'serpapi'.")
