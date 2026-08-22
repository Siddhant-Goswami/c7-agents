"""Run this BEFORE the lecture starts. Takes about ten seconds.

    python setup_check.py

If it prints OK three times, you can follow along tonight without touching
anything else. If it fails, fix it now, not at minute four of the session.
"""

print("1/3  imports ... ", end="", flush=True)
try:
    from agent_lab.llm import MODEL, llm
    from agent_lab.tools import get_august_rainfall, get_weather
except Exception as error:  # noqa: BLE001
    raise SystemExit(f"FAILED\n\n{error}\n\nTry: pip install -r requirements.txt")
print("OK")

print("2/3  weather API ... ", end="", flush=True)
now = get_weather("Bangalore")
past = get_august_rainfall("Bangalore", 2023)
print(f"OK  ({now['temperature_c']}°C now, {len(past['weekends'])} weekends found in Aug 2023)")

print(f"3/3  llm ({MODEL}) ... ", end="", flush=True)
reply = llm("Reply with exactly one word: ready")
print(f"OK  (model said: {reply!r})")

print("\nYou are set. See you in the lecture.")
