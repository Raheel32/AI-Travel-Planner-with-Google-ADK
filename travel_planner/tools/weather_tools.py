"""Weather via Open-Meteo (free, no API key)."""
from __future__ import annotations

import httpx

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


async def get_weather_forecast(city: str, start_date: str, end_date: str) -> dict:
    """Get the daily weather forecast for a city between two dates.

    Args:
        city: City name, e.g. "Istanbul".
        start_date: First day, YYYY-MM-DD.
        end_date: Last day, YYYY-MM-DD.

    Returns:
        A dict. `available` is False when no forecast exists (forecasts only
        reach roughly 16 days ahead); then `note` explains what to do instead.
    """
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            geo = await client.get(GEO_URL, params={"name": city, "count": 1, "language": "en"})
            geo.raise_for_status()
            results = geo.json().get("results") or []
            if not results:
                return {"available": False, "note": f"Could not locate '{city}'."}
            place = results[0]
            fc = await client.get(FORECAST_URL, params={
                "latitude": place["latitude"], "longitude": place["longitude"],
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "start_date": start_date, "end_date": end_date, "timezone": "auto",
            })
            if fc.status_code != 200:
                return {
                    "available": False,
                    "note": "No forecast for these dates (Open-Meteo only covers about the next 16 days). "
                            "Describe typical seasonal weather instead and say it is not a forecast.",
                }
            daily = fc.json().get("daily", {})
    except httpx.HTTPError as exc:
        return {"available": False, "note": f"Weather service unreachable ({type(exc).__name__})."}

    days = [
        {"date": d, "max_c": hi, "min_c": lo, "rain_chance_percent": rain}
        for d, hi, lo, rain in zip(
            daily.get("time", []), daily.get("temperature_2m_max", []),
            daily.get("temperature_2m_min", []), daily.get("precipitation_probability_max", []),
        )
    ]
    return {"available": True, "city": place.get("name", city), "country": place.get("country"), "days": days}
