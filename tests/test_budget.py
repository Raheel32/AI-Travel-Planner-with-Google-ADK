from travel_planner.tools.budget_tools import calculate_trip_budget


def test_within_budget():
    r = calculate_trip_budget(300, 50, 5, 2, 5000)
    # flights 600 + hotel 50*5*1 + 6 days * 2 travelers * (30+10+20) = 600+250+720 = 1570; +10% = 1727
    assert r["total_estimated_cost"] == 1727.0
    assert r["within_budget"] is True
    assert r["suggestions"] == []


def test_over_budget_gives_suggestions():
    r = calculate_trip_budget(900, 200, 5, 2, 1500)
    assert r["within_budget"] is False
    assert r["difference_from_budget"] < 0
    assert r["suggestions"]


def test_rooms_round_up_for_odd_travelers():
    r = calculate_trip_budget(0, 100, 2, 3, 10_000)
    assert r["breakdown"]["hotel"] == 100 * 2 * 2  # 3 travelers -> 2 rooms


def test_invalid_input_returns_error():
    assert "error" in calculate_trip_budget(100, 50, 0, 2, 1000)
    assert "error" in calculate_trip_budget(-1, 50, 3, 2, 1000)
