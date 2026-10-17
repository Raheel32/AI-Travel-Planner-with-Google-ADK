"""End-to-end test of the whole agent tree with a scripted FAKE model (no API key, no network).

It proves the plumbing works: the root saves the trip request, the parallel
researchers read it, the budget agent sees their output, and the itinerary agent
receives everything. It does NOT test Gemini's real behaviour.
"""
import asyncio
import json
import warnings

from google.adk.models import BaseLlm, LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types

from travel_planner import config
from travel_planner.agent import root_agent

warnings.filterwarnings("ignore", category=DeprecationWarning)

TRIP_ARGS = dict(
    origin_city="Karachi", origin_airport="KHI", destination_city="Istanbul",
    destination_airport="IST", departure_date="2030-04-10", return_date="2030-04-15",
    travelers=2, budget=2500, currency="USD", interests=["food", "history"],
)


def _call(name, args):
    return types.Part(function_call=types.FunctionCall(name=name, args=args))


def _text(t):
    return types.Part(text=t)


def _has_response(request, fn_name):
    return any(
        p.function_response and p.function_response.name == fn_name
        for c in request.contents for p in (c.parts or [])
    )


class ScriptedLlm(BaseLlm):
    model: str = "scripted"
    seen_itinerary_prompt: str = ""

    async def generate_content_async(self, llm_request, stream=False):
        sys = str(llm_request.config.system_instruction)
        if "Travel Coordinator" in sys:
            if _has_response(llm_request, "transfer_to_agent"):
                parts = [_text("done")]
            elif _has_response(llm_request, "save_trip_request"):
                parts = [_call("transfer_to_agent", {"agent_name": "trip_pipeline"})]
            else:
                parts = [_call("save_trip_request", TRIP_ARGS)]
        elif "Flight Research Agent" in sys:
            parts = [_text("Flights ok.\nCHEAPEST_FLIGHT_PRICE_PER_TRAVELER: 300")] \
                if _has_response(llm_request, "search_flights") else [_call("search_flights", {})]
        elif "Hotel Research Agent" in sys:
            parts = [_text("Hotels ok.\nCHEAPEST_HOTEL_RATE_PER_NIGHT: 60")] \
                if _has_response(llm_request, "search_hotels") else [_call("search_hotels", {})]
        elif "Destination Research Agent" in sys:
            parts = [_text("Weather mild. Visit Hagia Sophia.")]
        elif "Budget Agent" in sys:
            parts = [_text("Budget ok.")] if _has_response(llm_request, "calculate_trip_budget") else [
                _call("calculate_trip_budget", dict(flight_price_per_traveler=300, hotel_rate_per_night=60,
                                                    nights=5, travelers=2, budget=2500))]
        elif "Itinerary Planning Agent" in sys:
            ScriptedLlm.seen_itinerary_prompt = sys
            parts = [_text("FINAL PLAN")]
        else:
            parts = [_text("??? unknown agent")]
        yield LlmResponse(content=types.Content(role="model", parts=parts))


def _swap_models(agent, llm):
    if hasattr(agent, "model"):
        agent.model = llm
    for sub in agent.sub_agents:
        _swap_models(sub, llm)


def test_full_pipeline_with_scripted_model(monkeypatch):
    monkeypatch.setattr(config, "DATA_PROVIDER", "mock")
    _swap_models(root_agent, ScriptedLlm())

    async def run():
        runner = InMemoryRunner(agent=root_agent, app_name="travel_test")
        session = await runner.session_service.create_session(app_name="travel_test", user_id="u")
        msg = types.Content(role="user", parts=[types.Part(text="Plan a trip to Istanbul")])
        authors = []
        async for ev in runner.run_async(user_id="u", session_id=session.id, new_message=msg):
            authors.append(ev.author)
        final = await runner.session_service.get_session(
            app_name="travel_test", user_id="u", session_id=session.id)
        return authors, final.state

    authors, state = asyncio.run(run())

    assert json.loads(state["trip_request"])["destination_airport"] == "IST"
    assert "Flights ok" in state["flight_results"]
    assert "Hotels ok" in state["hotel_results"]
    assert "Hagia Sophia" in state["destination_results"]
    assert state["final_plan"] == "FINAL PLAN"
    # The itinerary agent's prompt must contain the earlier agents' outputs and the real budget tool result.
    prompt = ScriptedLlm.seen_itinerary_prompt
    assert "Flights ok" in prompt and "Hotels ok" in prompt and "Hagia Sophia" in prompt and "Budget ok" in prompt
    assert authors.index("flight_agent") < authors.index("budget_agent") < authors.index("itinerary_agent")
