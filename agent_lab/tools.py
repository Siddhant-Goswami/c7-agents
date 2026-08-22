"""The deterministic half. Given to you, not derived.

Two tools that hit a real weather API (Open-Meteo — free, no key, no signup).

Read these once and then forget them. They have no intelligence and no
flexibility: they do exactly what the instructions say, every single time.
That is the entire point of the deterministic half.

Responses are cached to .cache/ so that re-running a step during the lecture
is instant and does not depend on the conference wifi.
"""

import json
import os
import statistics
from datetime import date, timedelta

import requests

_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache")
_TIMEOUT = 20


# ──────────────────────────────────────────────────────────────────────────
# plumbing
# ──────────────────────────────────────────────────────────────────────────

def _cached_get(url: str, params: dict) -> dict:
    os.makedirs(_CACHE_DIR, exist_ok=True)
    key = str(abs(hash((url, json.dumps(params, sort_keys=True)))))
    path = os.path.join(_CACHE_DIR, f"{key}.json")

    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)

    response = requests.get(url, params=params, timeout=_TIMEOUT)
    response.raise_for_status()
    payload = response.json()

    with open(path, "w") as f:
        json.dump(payload, f)
    return payload


# The geocoder does not know that Bangalore and Bengaluru are the same place.
# Searching "Bangalore" returns exactly one hit: a neighbourhood in Karachi.
# It would have handed us real, correct-looking, 200-OK rainfall data for the
# wrong country — which is the single best argument in this repo for why a
# RESULT is not the same thing as an OBSERVATION.
_ALIASES = {
    "bangalore": "Bengaluru",
    "bombay": "Mumbai",
    "calcutta": "Kolkata",
    "madras": "Chennai",
    "poona": "Pune",
}


def _geocode(city: str) -> dict:
    """Resolve a city name to coordinates. Most populous match wins."""
    query = _ALIASES.get(city.strip().lower(), city.strip())
    data = _cached_get(
        "https://geocoding-api.open-meteo.com/v1/search",
        {"name": query, "count": 10, "language": "en", "format": "json"},
    )
    results = data.get("results")
    if not results:
        raise ValueError(f"Unknown city: {city!r}")

    hit = max(results, key=lambda r: r.get("population") or 0)
    return {
        "lat": hit["latitude"],
        "lon": hit["longitude"],
        "name": hit["name"],
        "country": hit.get("country", "?"),
    }


# ──────────────────────────────────────────────────────────────────────────
# the tools themselves
# ──────────────────────────────────────────────────────────────────────────

def get_weather(city: str) -> dict:
    """Current weather for a city. One call, one answer, one step.

    This is the tool you already built in Module 2.
    """
    place = _geocode(city)
    data = _cached_get(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": place["lat"],
            "longitude": place["lon"],
            "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
            "timezone": "auto",
        },
    )
    current = data["current"]
    return {
        "city": f"{place['name']}, {place['country']}",
        "temperature_c": current["temperature_2m"],
        "humidity_pct": current["relative_humidity_2m"],
        "precipitation_mm": current["precipitation"],
        "wind_kmh": current["wind_speed_10m"],
        "observed_at": current["time"],
    }


def get_august_rainfall(city: str, year: int) -> dict:
    """Total rainfall for every August weekend of ONE year, in one city.

    Note the shape of this tool carefully. It answers for a single year.
    The goal we are chasing tonight spans ten of them. That gap between
    'what one tool call returns' and 'what the goal needs' is where the
    whole lecture happens.
    """
    this_year = date.today().year
    if not (1960 <= year <= this_year):
        raise ValueError(f"Year {year} is out of range (1960..{this_year}).")
    if year >= this_year and date.today() < date(this_year, 9, 5):
        raise ValueError(
            f"August {year} is not finished (or not yet published). "
            f"Ask for {this_year - 1} or earlier."
        )

    place = _geocode(city)
    data = _cached_get(
        "https://archive-api.open-meteo.com/v1/archive",
        {
            "latitude": place["lat"],
            "longitude": place["lon"],
            "start_date": f"{year}-08-01",
            "end_date": f"{year}-08-31",
            "daily": "precipitation_sum",
            "timezone": "auto",
        },
    )

    daily = dict(zip(data["daily"]["time"], data["daily"]["precipitation_sum"]))

    weekends = []
    day = date(year, 8, 1)
    while day <= date(year, 8, 31):
        if day.weekday() == 5:  # Saturday
            sunday = day + timedelta(days=1)
            sat_mm = daily.get(day.isoformat()) or 0.0
            sun_mm = daily.get(sunday.isoformat()) or 0.0
            same_month = sunday.month == day.month
            label = (
                f"{day.strftime('%b %-d')}-{sunday.strftime('%-d')}"
                if same_month
                else f"{day.strftime('%b %-d')}-{sunday.strftime('%b %-d')}"
            )
            weekends.append(
                {
                    "weekend": label,
                    "saturday": day.isoformat(),
                    "sunday": sunday.isoformat(),
                    "rain_mm": round(sat_mm + sun_mm, 1),
                }
            )
        day += timedelta(days=1)

    values = [w["rain_mm"] for w in weekends]
    return {
        "city": f"{place['name']}, {place['country']}",
        "year": year,
        "weekends": weekends,
        "month_total_mm": round(sum(v for v in daily.values() if v), 1),
        "wettest_weekend": max(weekends, key=lambda w: w["rain_mm"])["weekend"],
        "driest_weekend": min(weekends, key=lambda w: w["rain_mm"])["weekend"],
        "median_weekend_mm": round(statistics.median(values), 1),
    }
