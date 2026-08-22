"""
STEP 3 — The two missing pieces, and the name of the thing you built
═════════════════════════════════════════════════════════════════════

    python3 step3_agent.py

Your Q3 answer was probably two functions shaped like this:

    something that interprets what just happened
    something that decides whether we are finished

That is exactly right, and they are the last two pieces. Add them and the
loop closes — the program stops being a countdown and starts being able to
end itself on purpose.

Watch for one detail as it runs, because it is the whole difference between
this file and step 2: the loop does not finish because it ran out of budget.
It finishes because something looked at the evidence and said "I have it."
"""

from step1_one_shot import GOAL, TOOLS, llm, llm_json, rule

MAX_STEPS = 5


# ══════════════════════════════════════════════════════════════════════════
#  THE FIVE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════

def sense(goal, history):
    """Construct the relevant situation. This is context engineering, as a step.

    A Roomba with a perfect cleaning algorithm and no sensor cleans nothing.
    Perception comes before planning.

    Note what this returns: a short SUMMARY. Summaries are lossy — remember
    that when you get to experiment 2 at the bottom of this file.
    """
    return llm(
        "You are the SENSE step of an agent loop.\n"
        "Describe the CURRENT SITUATION in 2-3 lines. Do not plan. Do not act.\n"
        "State what is known so far and what is still unknown.\n\n"
        f"GOAL: {goal}\n"
        f"HISTORY ({len(history)} steps): {history or 'nothing has happened yet'}\n"
    )


def plan(goal, history):
    """Propose the single next action. Sequence is part of correctness."""
    return llm_json(
        "You are the PLAN step of an agent loop. Propose the SINGLE next tool call.\n\n"
        "TOOLS (only these exist):\n"
        '  get_ticket    args {"ticket_id":"T-…"}    -> {subject, filed_by}\n'
        '  get_employee  args {"employee_id":"E-…"}  -> {name, manager}\n\n'
        "RULE: never repeat a call whose args already appear in HISTORY —\n"
        "that result is already known.\n\n"
        'Return JSON exactly: {"thought":"…","tool":"…","args":{…}}\n\n'
        f"GOAL: {goal}\n"
        f"HISTORY: {history}\n"
    )


def act(action):
    """Touch the world. The only line in this file that does."""
    name, args = action.get("tool"), action.get("args") or {}
    if name not in TOOLS:
        return {"error": f"no such tool {name!r}. allowed: {list(TOOLS)}"}
    try:
        return TOOLS[name](**args)
    except Exception as error:
        return {"error": f"{type(error).__name__}: {error}"}


def observe(goal, action, result):
    """Turn a RESULT into an OBSERVATION. These are not the same thing.

    A result is bytes that came back. An observation is what those bytes mean
    for the goal. A 200 OK containing the wrong city is still a 200 OK — only
    this step can catch that.
    """
    return llm(
        "You are the OBSERVE step of an agent loop.\n"
        "In 1-2 lines state ONLY what was learned and whether it moves the goal\n"
        "forward. Say so explicitly if the result was an error, empty, or off-target.\n\n"
        f"GOAL: {goal}\n"
        f"ACTION: {action}\n"
        f"RESULT: {result}\n"
    )


def reflect(goal, history, observation):
    """Decide whether the loop continues. This is the whole ballgame.

    Look at the signature: it receives HISTORY — everything that has happened,
    raw. Not a summary of it. A step that decides whether you are finished
    cannot do that job on a paraphrase of the evidence.

    Note also what it returns: ONE field. Not {"done": bool, "answer": str},
    because two fields that can contradict each other eventually will — a
    model will happily hand you {"done": false, "answer": "Devika Nair"}.
    Ask for one thing, and `if answer:` is unambiguous.
    """
    return llm_json(
        "You are the REFLECT step of an agent loop. You alone decide whether the loop stops.\n\n"
        'Return JSON exactly: {"answer": "<the answer>"} if HISTORY is sufficient,\n'
        'otherwise {"answer": null, "missing": "what is still needed"}\n\n'
        "RULES:\n"
        '- `answer` must be a person\'s NAME copied from a "name" field. Never an ID like "E-04".\n'
        '- The manager of X is the employee whose id equals X\'s "manager" field.\n'
        "  You need THAT employee's name.\n"
        "- If that name is not in HISTORY yet, answer MUST be null.\n\n"
        f"GOAL: {goal}\n"
        f"HISTORY: {history}\n"
        f"LATEST OBSERVATION: {observation}\n"
    )


# ══════════════════════════════════════════════════════════════════════════
#  THE AGENT — this is the whole thing
# ══════════════════════════════════════════════════════════════════════════

def run(goal, max_steps=MAX_STEPS, verbose=True):
    history = []

    for step in range(max_steps):
        situation = sense(goal, history)
        action = plan(goal, history)
        result = act(action)

        # Record what happened BEFORE anything judges it. Get this order wrong
        # and reflect() decides whether you are finished while looking at a
        # history that is missing the step you just took — so it judges the
        # newest evidence only through observe()'s paraphrase of it.
        history.append({"step": step + 1, "tool": action.get("tool"),
                        "args": action.get("args"), "result": result})

        observation = observe(goal, action, result)
        reflection = reflect(goal, history, observation)

        if verbose:
            rule(f"ITERATION {step + 1} of {max_steps}")
            print(f"  SENSE    {situation}")
            print(f"  PLAN     {action.get('tool')}({action.get('args')})   — {action.get('thought','')}")
            print(f"  ACT      {result}")
            print(f"  OBSERVE  {observation}")
            print(f"  REFLECT  {reflection}")

        if reflection.get("answer"):
            return reflection["answer"], step + 1

    return None, max_steps


if __name__ == "__main__":
    print(f"GOAL: {GOAL}")
    answer, used = run(GOAL)

    rule("RESULT")
    if answer:
        print(f"  {answer}\n\n  Reached in {used} iterations, out of a budget of {MAX_STEPS}.")
        print("  The loop did not run out. It STOPPED, because something decided it was done.")
    else:
        print(f"  No answer. The stopping condition fired after {MAX_STEPS} iterations.")
        print("  That is not a bug — that is the boundary you wrote in step 2 doing its job.")


# ══════════════════════════════════════════════════════════════════════════
#  NOW NAME WHAT YOU BUILT
# ══════════════════════════════════════════════════════════════════════════
#
#      SENSE.  PLAN.  ACT.  OBSERVE.  REFLECT.        (+ the STOP around it)
#
# We did not open with that diagram, because five boxes handed to you up
# front are five boxes to memorise. Every one of them appeared here only
# after the program hit a specific problem:
#
#     we needed a boundary                    →  the STOP appeared    (step 2)
#     we needed another attempt               →  the LOOP appeared    (step 2)
#     we needed turn 2 to differ from turn 1  →  STATE appeared       (step 2)
#     we needed to know where we are          →  SENSE appeared
#     we needed the sequence to be decided    →  PLAN appeared
#     we needed to touch the world safely     →  ACT appeared
#     we needed the CONSEQUENCE, not the bytes→  OBSERVE appeared
#     we needed someone to answer "and now?"  →  REFLECT appeared
#
# So this is not an arbitrary framework. Delete any one box and you can name
# exactly which failure comes back. That is the test of whether you own it.
#
#           ┌──────────────────────────────────┐
#           │                                  │
#           ▼                                  │
#     SENSE → PLAN → ACT → OBSERVE → REFLECT ──┤
#                                        │     │
#                                    answer?   │
#                                      /   \   │
#                                    yes    no ┘
#                                     │
#                                    STOP
#
# ── THREE EXPERIMENTS. Do them now; each is one line. ─────────────────────
#
#   1. STOP.     Set max_steps=2 and run. Does it stop cleanly, or does it
#                claim a false answer? Whose fault is that outcome — the
#                model's, or yours?
#
#   2. SENSE.    In run(), pass `situation` to plan() and reflect() INSTEAD
#                of `history`. The memory still exists; nothing reads it
#                raw any more. Predict what breaks before you run it.
#                (This is the single most common real-world agent bug: the
#                step that decides whether you are done is looking at a
#                summary of the evidence instead of the evidence.)
#
#   3. REFLECT.  Delete the `if reflection.get("answer")` branch. Reflection
#                is still computed, still printed, and now decides nothing.
#                What species of software is this now? Compare it to step 2.
#
# ── THE SDK REVEAL ────────────────────────────────────────────────────────
#
#     agent = Agent(model=model, tools=tools, instructions=instructions)
#     result = agent.run(goal)
#
#   Q. What disappeared?
#        history · the loop · tool dispatch · structured output · the
#        stopping condition · context management
#
#   Q. Did the LOOP disappear?
#        No. You stopped writing it. That is what an abstraction IS.
#
#   Q. When does that abstraction become dangerous?
#        → when you no longer understand the assumptions it is hiding.
#          You just wrote all of them by hand. You can now go and ask.
#
# ── AND THE CODING AGENTS YOU USE EVERY DAY ───────────────────────────────
#
#   Zoom into any ten seconds of Claude Code or Codex working. What files
#   exist, what did the user ask, what failed → it SENSES. It decides what
#   to edit → PLANS. It edits → ACTS. It reads the test output → OBSERVES.
#   It decides whether to try again → REFLECTS.
#
#   Same shape. Vastly better engineering inside each box. That is why we
#   learned the primitive before the product: agent products become things
#   you can reverse-engineer, instead of things you have to trust.
#
#   "What did we give the LLM that turned it into an agent?"
#
#   Not a bigger model. Not another tool. We gave it a mechanism for
#   experiencing the consequence of one decision and using that consequence
#   to make the next one. That mechanism is the loop.
