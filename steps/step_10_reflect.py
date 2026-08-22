"""
STEP 10 — Discovery 7 of 7:  REFLECT, and the loop closes
════════════════════════════════════════════════════════

    python steps/step_10_reflect.py

If you answered "an evaluator", or "check it against the goal" — both are
right, and both force something this lab has left unstated the whole way:
you cannot evaluate anything without a GOAL.

But an evaluator gives you a verdict, not a next move. Something still has to
decide what more is needed — which is the exact question this module opened
with. So: one more LLM pass, looking back over everything that happened.

    reflection = reflect(goal, state, plan, observation)

Give it a contract the program can branch on:

    {"done": false, "next": "fetch the next missing year", "answer": null}
    {"done": true,  "next": null, "answer": "..."}

Until this line, the model participated in the workflow.
At this line, the model can decide whether the workflow continues.

That is where "what happens next?" leaves the human.
"""

from lab import get_august_rainfall, get_weather, llm, llm_json, rule, show

# Scaled to five years so a full run finishes inside a lecture slot.
# step_12 asks you to put it back to ten and watch what breaks.
GOAL = (
    "Find the August weekend in Bangalore least likely to rain, using rainfall "
    "data for the last 5 Augusts (2021, 2022, 2023, 2024, 2025). Compare the "
    "same calendar weekend across all five years before concluding."
)
MAX_STEPS = 8

TOOL_MENU = {
    "august_rainfall": "args {city, year} — August weekend-by-weekend rainfall, ONE city, ONE year (1960-2025)",
    "current_weather": "args {city} — today's weather, right now",
}
TOOLS = {"august_rainfall": get_august_rainfall, "current_weather": get_weather}


def sense(goal, history, tool_menu):
    return llm(
        "You are the SENSE step of an agent loop.\n"
        "Describe the CURRENT SITUATION in 3-4 lines. Do not plan. Do not act.\n"
        "State exactly which years have already been fetched and which are missing.\n\n"
        f"GOAL: {goal}\n"
        f"TOOLS AVAILABLE: {tool_menu}\n"
        f"HISTORY SO FAR ({len(history)} steps): {history or 'nothing has happened yet'}\n"
    )


def plan(goal, state, tool_menu):
    return llm_json(
        "You are the PLAN step of an agent loop.\n"
        "Return JSON exactly like:\n"
        '{"steps": ["...", "..."], "next": {"tool": "<tool name>", "args": {...}}}\n\n'
        "Rules:\n"
        "- `steps` is the full ordered sequence still needed to reach the goal.\n"
        "- `next` is the SINGLE next action, and its tool must be one of the tools listed.\n"
        "- Never repeat an action already present in the state.\n\n"
        f"GOAL: {goal}\n"
        f"TOOLS AVAILABLE: {tool_menu}\n"
        f"CURRENT STATE: {state}\n"
    )


def act(the_plan, tools):
    action = the_plan.get("next") or {}
    name, args = action.get("tool"), action.get("args") or {}
    if name not in tools:
        return {"ok": False, "error": f"No such tool {name!r}. Allowed: {list(tools)}"}
    try:
        return {"ok": True, "data": tools[name](**args)}
    except Exception as error:  # noqa: BLE001
        return {"ok": False, "error": f"{type(error).__name__}: {error}"}


def observe(goal, action, result):
    return llm(
        "You are the OBSERVE step of an agent loop.\n"
        "In 2-3 lines, state ONLY what was learned and whether it moves the goal forward.\n"
        "Be explicit if the result was empty, an error, off-target, or insufficient.\n"
        "If rainfall data came back, list each weekend and its rain_mm compactly.\n\n"
        f"GOAL: {goal}\n"
        f"ACTION TAKEN: {action}\n"
        f"RAW RESULT: {str(result)[:2000]}\n"
    )


def reflect(goal, state, the_plan, observation):
    """The step that decides whether the loop continues. The whole ballgame."""
    return llm_json(
        "You are the REFLECT step of an agent loop. You decide what happens next.\n"
        'Return JSON exactly like: {"done": true/false, "next": "..." or null, "answer": "..." or null}\n\n'
        "Set done=true ONLY if the goal is fully satisfied by evidence already gathered.\n"
        "If done=true, `answer` must contain the final answer for the user.\n"
        "If done=false, `next` says in one line what still has to happen.\n"
        "Do not claim done because you are running low on steps.\n\n"
        f"GOAL: {goal}\n"
        f"STATE AT START OF THIS STEP: {state}\n"
        f"PLAN THIS STEP: {the_plan}\n"
        f"OBSERVATION THIS STEP: {observation}\n"
    )


history = []
final_answer = None

for step in range(MAX_STEPS):
    rule(f"ITERATION {step + 1} of {MAX_STEPS}")

    state = sense(GOAL, history, TOOL_MENU)
    the_plan = plan(GOAL, state, TOOL_MENU)
    result = act(the_plan, TOOLS)
    observation = observe(GOAL, the_plan.get("next"), result)
    reflection = reflect(GOAL, state, the_plan, observation)

    show("ACTION", the_plan.get("next"))
    show("OBSERVATION", observation)
    show("REFLECTION", reflection)

    # Carry everything forward. This is what makes the next turn a different turn.
    history.append(
        {
            "step": step + 1,
            "action": the_plan.get("next"),
            "observation": observation,
            "reflection": reflection,
        }
    )

    if reflection.get("done"):
        final_answer = reflection.get("answer")
        break

rule("RESULT")
if final_answer:
    print(final_answer)
else:
    print(f"Stopping condition fired after {MAX_STEPS} steps. No final answer.")
    print("That is not a bug. That is the boundary you designed in step_03 doing its job.")


# ══════════════════════════════════════════════════════════════════════════
# WATCH IT RUN. After every iteration, answer:
# ══════════════════════════════════════════════════════════════════════════
#
#   Q1. What changed between this iteration and the last?
#           → the state
#   Q2. What caused the state to change?
#           → the consequences of the previous action
#   Q3. What caused the BEHAVIOUR to change?
#           → the model saw the changed state
#
# Draw it:
#
#           ┌──────────────────────────────────┐
#           │                                  │
#           ▼                                  │
#     SENSE → PLAN → ACT → OBSERVE → REFLECT ──┤
#                                        │     │
#                                      done?   │
#                                      /   \   │
#                                    yes    no ┘
#                                     │
#                                    STOP
#
# Now open step_11 — and only now does the thing you built get a name.
