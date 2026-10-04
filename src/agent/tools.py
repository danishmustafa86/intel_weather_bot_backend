"""Tools the agent can call: current weather (OpenWeather) and web search (Tavily)."""

import httpx
from langchain_core.tools import tool
from tavily import AsyncTavilyClient

from src.config import get_settings

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


@tool
async def get_current_weather(location: str, units: str = "metric") -> str:
    """Get the CURRENT weather for a city or place anywhere in the world.

    Args:
        location: City name, optionally with country code, e.g. "London",
            "Lahore,PK", "Paris,FR", "New York,US".
        units: "metric" (Celsius), "imperial" (Fahrenheit) or "standard" (Kelvin).
    """
    api_key = get_settings().openweather_api_key
    if not api_key:
        return "Weather service is not configured (OPENWEATHER_API_KEY missing)."

    params = {"q": location, "appid": api_key, "units": units}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(OPENWEATHER_URL, params=params)
    except httpx.HTTPError as exc:
        return f"Could not reach the weather service: {exc}"

    if resp.status_code == 404:
        return f"Location '{location}' was not found. Try adding a country code, e.g. 'Lahore,PK'."
    if resp.status_code == 401:
        return "Weather service rejected the API key (it may be invalid or not yet active)."
    if resp.status_code != 200:
        return f"Weather service error {resp.status_code}: {resp.text[:200]}"

    d = resp.json()
    unit = {"metric": "°C", "imperial": "°F"}.get(units, "K")
    wind_unit = "mph" if units == "imperial" else "m/s"
    main, wind = d.get("main", {}), d.get("wind", {})
    description = ", ".join(w["description"] for w in d.get("weather", []))
    place = f"{d.get('name')}, {d.get('sys', {}).get('country', '')}".strip(", ")

    return (
        f"Current weather in {place}:\n"
        f"- Conditions: {description}\n"
        f"- Temperature: {main.get('temp')}{unit} (feels like {main.get('feels_like')}{unit})\n"
        f"- Min/Max: {main.get('temp_min')}{unit} / {main.get('temp_max')}{unit}\n"
        f"- Humidity: {main.get('humidity')}%\n"
        f"- Pressure: {main.get('pressure')} hPa\n"
        f"- Wind: {wind.get('speed')} {wind_unit}\n"
        f"- Cloudiness: {d.get('clouds', {}).get('all')}%\n"
        f"- Visibility: {d.get('visibility', 'n/a')} m"
    )


@tool
async def web_search(query: str) -> str:
    """Search the web for up-to-date information on any topic (news, facts,
    people, events, prices, how-to, etc.). Use this for any question that
    is not about the current weather.

    Args:
        query: A clear, specific search query.
    """
    api_key = get_settings().tavily_api_key
    if not api_key:
        return "Web search is not configured (TAVILY_API_KEY missing)."

    try:
        client = AsyncTavilyClient(api_key=api_key)
        result = await client.search(query=query, max_results=5, include_answer=True)
    except Exception as exc:
        return f"Web search failed: {exc}"

    lines = []
    if result.get("answer"):
        lines.append(f"Summary: {result['answer']}\n")
    for i, r in enumerate(result.get("results", []), start=1):
        lines.append(f"[{i}] {r.get('title')}\nURL: {r.get('url')}\n{r.get('content', '')[:600]}\n")
    return "\n".join(lines) or "No results found."


TOOLS = [get_current_weather, web_search]
