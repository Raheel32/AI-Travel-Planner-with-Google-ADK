"""Budget maths in plain Python. LLMs must NOT do money arithmetic themselves."""
from __future__ import annotations

import math


def calculate_trip_budget(
    flight_price_per_traveler: float,
    hotel_rate_per_night: float,
    nights: int,
    travelers: int,
    budget: float,
    daily_food_per_traveler: float = 30.0,
    daily_local_transport_per_traveler: float = 10.0,
    daily_activities_per_traveler: float = 20.0,
    contingency_percent: float = 10.0,
) -> dict:
    """Calculate the estimated total trip cost and compare it with the budget.

    Assumptions (stated in the result): 2 travelers share one room, and
    food/transport/activities are counted for nights + 1 days.

    Args:
        flight_price_per_traveler: Cheapest round-trip flight price per traveler (0 if unknown).
        hotel_rate_per_night: Cheapest hotel price per room per night (0 if unknown).
        nights: Number of nights.
        travelers: Number of travelers.
        budget: The user's total budget.
        daily_food_per_traveler: Estimated food cost per traveler per day.
        daily_local_transport_per_traveler: Estimated local transport per traveler per day.
        daily_activities_per_traveler: Estimated activities/entry fees per traveler per day.
        contingency_percent: Safety margin added on top of the subtotal.

    Returns:
        A dict with a cost breakdown, total, difference from budget, a
        within_budget flag, and suggestions when over budget.
    """
    if nights < 1 or travelers < 1 or budget <= 0:
        return {"error": "nights, travelers and budget must all be positive."}
    if min(flight_price_per_traveler, hotel_rate_per_night, daily_food_per_traveler,
           daily_local_transport_per_traveler, daily_activities_per_traveler, contingency_percent) < 0:
        return {"error": "Costs cannot be negative."}

    rooms = math.ceil(travelers / 2)
    days = nights + 1
    flights = flight_price_per_traveler * travelers
    hotel = hotel_rate_per_night * nights * rooms
    food = daily_food_per_traveler * travelers * days
    transport = daily_local_transport_per_traveler * travelers * days
    activities = daily_activities_per_traveler * travelers * days
    subtotal = flights + hotel + food + transport + activities
    contingency = subtotal * contingency_percent / 100
    total = subtotal + contingency
    difference = budget - total

    suggestions: list[str] = []
    if difference < 0:
        suggestions.append(f"Over budget by {abs(difference):.2f}.")
        other_costs = flights + food + transport + activities
        affordable = (budget / (1 + contingency_percent / 100) - other_costs) / (nights * rooms)
        if affordable > 0:
            suggestions.append(f"Hotel would need to cost about {affordable:.2f} per room per night to fit.")
        else:
            suggestions.append("Even a free hotel would not fit: consider other dates, a closer destination, or a higher budget.")
        suggestions.append("Other levers: shift travel dates, accept a connecting flight, or trim paid activities.")

    return {
        "assumptions": f"{rooms} room(s); {days} days of daily costs; {contingency_percent:.0f}% contingency",
        "breakdown": {
            "flights": round(flights, 2), "hotel": round(hotel, 2), "food": round(food, 2),
            "local_transport": round(transport, 2), "activities": round(activities, 2),
            "contingency": round(contingency, 2),
        },
        "total_estimated_cost": round(total, 2),
        "budget": round(budget, 2),
        "difference_from_budget": round(difference, 2),
        "percent_of_budget_used": round(total / budget * 100, 1),
        "within_budget": difference >= 0,
        "suggestions": suggestions,
    }
