"""Pydantic models: the shared "data contract" between agents and tools.

Why? LLMs are sloppy with formats. Validating every trip request and every API
result with Pydantic catches bad dates, bad airport codes and missing fields
BEFORE they spread through the system.
"""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator


class TripRequest(BaseModel):
    origin_city: str
    origin_airport: str = Field(description="3-letter IATA code, e.g. KHI")
    destination_city: str
    destination_airport: str = Field(description="3-letter IATA code, e.g. IST")
    departure_date: date
    return_date: date
    travelers: int = Field(ge=1, le=9)
    budget: float = Field(gt=0, description="Total trip budget for all travelers")
    currency: str = "USD"
    interests: list[str] = Field(default_factory=list)

    @field_validator("origin_airport", "destination_airport")
    @classmethod
    def _check_iata(cls, v: str) -> str:
        v = v.strip().upper()
        if len(v) != 3 or not v.isalpha():
            raise ValueError("must be a 3-letter IATA airport code, e.g. KHI")
        return v

    @field_validator("currency")
    @classmethod
    def _check_currency(cls, v: str) -> str:
        v = v.strip().upper()
        if len(v) != 3 or not v.isalpha():
            raise ValueError("currency must be a 3-letter code, e.g. USD")
        return v

    @model_validator(mode="after")
    def _check_dates(self) -> "TripRequest":
        if self.return_date <= self.departure_date:
            raise ValueError("return_date must be after departure_date")
        return self

    @property
    def nights(self) -> int:
        return (self.return_date - self.departure_date).days


class FlightOption(BaseModel):
    airlines: list[str]
    flight_numbers: list[str] = Field(default_factory=list)
    price: float = Field(description="Price per traveler (assumed), in `currency`")
    currency: str
    stops: int
    total_duration_minutes: int | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    is_best: bool = False


class FlightSearchResult(BaseModel):
    provider: str
    retrieved_at: str
    currency: str
    options: list[FlightOption] = Field(default_factory=list)
    cheapest_price_per_traveler: float | None = None
    note: str | None = None
    error: str | None = None


class HotelOption(BaseModel):
    name: str
    rate_per_night: float = Field(description="Per room, per night, in `currency`")
    total_rate: float | None = None
    currency: str
    rating: float | None = None
    hotel_class: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    amenities: list[str] = Field(default_factory=list)
    link: str | None = None


class HotelSearchResult(BaseModel):
    provider: str
    retrieved_at: str
    currency: str
    options: list[HotelOption] = Field(default_factory=list)
    cheapest_rate_per_night: float | None = None
    note: str | None = None
    error: str | None = None
