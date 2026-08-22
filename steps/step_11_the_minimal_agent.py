"""
STEP 11 — Name what you built:  S P A O R
═════════════════════════════════════════

    python steps/step_11_the_minimal_agent.py

    SENSE.  PLAN.  ACT.  OBSERVE.  REFLECT.

This lab deliberately did not open with that diagram. Five boxes handed to
you up front are five boxes to memorise. Instead every box appeared here
because the program hit a specific problem:

    we needed the relevant state    →  SENSE appeared
    we needed sequence              →  PLAN appeared
    we needed to touch the world    →  ACT appeared
    we needed to understand the     →  OBSERVE appeared
      consequence
    we needed someone to answer     →  REFLECT appeared
      "what happens next?"
    we needed a boundary            →  the STOPPING CONDITION appeared

So this is not an arbitrary framework. Each abstraction exists because
removing it creates a specific failure mode. Delete any one of them and you
can name exactly which failure comes back.

The loop is at the top of this file, on purpose. Nineteen lines. This — not
LangChain, not an Agent SDK, not Claude Code, not Codex — is the thing to
burn into your head. Everything we study from here is either improving one of
these boxes, constraining one, connecting several, or hiding them behind a
better abstraction.
"""

from lab import get_august_rainfall, get_weather, llm, llm_json, rule, show

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


# ══════════════════════════════════════════════════════════════════════════
#  THE AGENT
# ══════════════════════════════════════════════════════════════════════════

def run(goal, tools=TOOLS, menu=TOOL_MENU, max_steps=MAX_STEPS, verbose=True):
    history = []

    for step in range(max_steps):
        state = sense(goal, history, menu)
        the_plan = plan(goal, state, menu)
        result = act(the_plan, tools)
        observation = observe(goal, the_plan.get("next"), result)
        reflection = reflect(goal, state, the_plan, observation)

        history.append(
            {
                "step": step + 1,
                "action": the_plan.get("next"),
                "observation": observation,
                "reflection": reflection,
            }
        )

        if verbose:
            rule(f"ITERATION {step + 1} of {max_steps}")
            show("ACTION", the_plan.get("next"))
            show("OBSERVATION", observation)
            show("DONE?", reflection.get("done"))

        if reflection.get("done"):
            return reflection.get("answer")

    return None


# ══════════════════════════════════════════════════════════════════════════
#  THE FIVE STEPS. Four of them are one LLM call. One of them is a dict lookup.
# ══════════════════════════════════════════════════════════════════════════

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


if __name__ == "__main__":
    answer = run(GOAL)
    rule("FINAL ANSWER")
    print(answer or "Stopping condition fired first. No answer. By design.")
