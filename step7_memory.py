"""
STEP 7. Failure: the agent worked something out on Tuesday and starts
Wednesday knowing nothing, so it pays for the same three lookups forever.

    python3 step7_memory.py --reset     wipe memory, then run both days
    python3 step7_memory.py             run both days again, already warm

State (step 5) survives a crash inside ONE task. Memory survives the task.
Same file format, completely different question:

    STATE   is this task finished?          scoped to a goal, deleted after
    MEMORY  what do I know about this job?  scoped to nothing, kept on purpose

This file writes SEMANTIC memory: durable facts about the domain. The other
two kinds are the same idea aimed differently. A skill file the agent follows
(how we escalate a P1) is PROCEDURAL memory. A timestamped log of what it did
on each run is EPISODIC. All three are text files a harness reads on the way
in. None of them are a database, and none of them need to be.
"""

import sys

from harness import (SCRATCH, TICKET_TOOLS, act, llm_json, plan, preview, reflect,
                     reset_usage, rule, show, tokens_used)

MAX_STEPS = 4
MEMORY_FILE = SCRATCH / "memory.md"

# The two goals are different questions about the same standing fact. That is
# the whole demo: day two is not a repeat, it is a question whose answer day
# one already paid to work out.
DAY_ONE = ("Ticket T-1002 is a Payments ticket. Find who filed it, then find the "
           "NAME of that person's manager. That manager owns Payments tickets. "
           "State the owner's name.")
DAY_TWO = ("A new Payments ticket arrived this morning. Which named person "
           "owns Payments tickets and should get it?")


# ══════════════════════════════════════════════════════════════════════════
#  THE NEW PIECE: a markdown file, read in and appended to
# ══════════════════════════════════════════════════════════════════════════

def load_memory():
    return MEMORY_FILE.read_text().strip() if MEMORY_FILE.exists() else ""


def update_memory(fact):
    with MEMORY_FILE.open("a") as handle:
        handle.write(f"- {fact}\n")


def learn(goal, history):
    """One bounded question at the end of a run, and one only.

    Bounded matters. "Write down anything useful" fills the file with this
    run's paperwork, and every future run then pays to read it and gets
    steered by it. The prompt below is mostly a list of things NOT to keep,
    which is the honest shape of a memory policy.
    """
    result = llm_json(
        "A run just finished. Name the ONE durable fact worth carrying into "
        "future runs, if any.\n\n"
        "It qualifies only if ALL of these hold:\n"
        "  - it is about the domain, not about this run\n"
        "  - it will still be true next week\n"
        "  - a future run would otherwise have to re-derive it from tools\n\n"
        "NEVER record: the goal you were given, the steps you took, ticket ids "
        "specific to this run, timings, or anything that changes daily.\n"
        "Write it as a standing fact a future run can apply directly, not as a "
        "note about what happened here.\n"
        'Return JSON exactly: {"fact":"<one sentence>"}, or {"fact":null} if\n'
        "nothing qualifies.\n\n"
        f"GOAL: {goal}\n"
        f"HISTORY: {history}\n",
        label="learn",
    )
    fact = result.get("fact")
    return fact if isinstance(fact, str) and fact.strip() else None


def run(goal, day):
    memory = load_memory()
    rule(day)
    print(f"  GOAL     {goal}")
    lines = memory.splitlines() or ["(empty, nothing was ever learned)"]
    for number, line in enumerate(lines):
        print(f"  {'MEMORY  ' if number == 0 else '        '} {line}")

    context = (f"WHAT YOU ALREADY KNOW (established by earlier runs, treat as "
               f"fact):\n{memory}\n\n") if memory else ""
    history, used = [], 0

    # Ask before acting. If memory already contains the answer, the cheapest
    # correct run is the one that makes no tool calls at all. An agent that
    # cannot notice it already knows something is an agent with a filing
    # cabinet it never opens.
    if memory:
        reflection = reflect(goal, history, extra=context + (
            "If WHAT YOU ALREADY KNOW answers the GOAL on its own, that counts "
            "as achieved even though HISTORY is empty.\n\n"))
        if reflection.get("answer"):
            print(f"  REFLECT  {preview(reflection)}")
            print("  finished from memory. Zero tool calls.")
            return reflection["answer"], 0

    for step in range(MAX_STEPS):
        action = plan(goal, history, TICKET_TOOLS, extra=context)
        result = act(action, TICKET_TOOLS)
        history.append({"step": step + 1, "tool": action.get("tool"),
                        "args": action.get("args") or {}, "result": result})
        used = step + 1

        rule(f"ITERATION {used} of {MAX_STEPS}")
        show(action, result)
        reflection = reflect(goal, history, extra=context)
        print(f"  REFLECT  {preview(reflection)}")
        if reflection.get("answer"):
            break

    answer = reflection.get("answer")

    # The write happens at the END, once, on the way out. Not per turn.
    fact = learn(goal, history)
    if fact:
        update_memory(fact)
        print(f"\n  LEARNED  {fact}")
        print("  appended to scratch/memory.md")
    else:
        print("\n  LEARNED  nothing durable. Correct answer sometimes.")
    return answer, used


if __name__ == "__main__":
    if "--reset" in sys.argv:
        MEMORY_FILE.unlink(missing_ok=True)
        print("scratch/memory.md wiped. This is the cold start.\n")

    reset_usage()
    answer_one, steps_one = run(DAY_ONE, "DAY ONE")
    cost_one = tokens_used()

    rule("WHAT IS IN scratch/memory.md NOW")
    print(load_memory() or "  (nothing)")

    reset_usage()
    answer_two, steps_two = run(DAY_TWO, "DAY TWO: new process, new goal, same file")
    cost_two = tokens_used()

    rule("RESULT")
    print(f"  day one: {answer_one}")
    print(f"           {steps_one} tool calls, {cost_one:,} tokens")
    print(f"  day two: {answer_two}")
    print(f"           {steps_two} tool calls, {cost_two:,} tokens")
    print("\n  Same model. Same tools. Day two is cheaper because a fact it had\n"
          "  already paid for was sitting in a text file when it started.\n"
          "  That is the entire mechanism, and it is a text file.")
    print("\n  Now open scratch/memory.md and read it as an adversary: if one wrong\n"
          "  line got in there, how many future runs inherit it, and what in this\n"
          "  program would ever catch it?")


# ══════════════════════════════════════════════════════════════════════════
# PREDICT before you open step 8
# ══════════════════════════════════════════════════════════════════════════
#
# Name one fact from this run that belongs in memory and one that must not go
# there. What goes wrong, over ten runs, if the second kind leaks in?
#
# Then, before you move on:
#
#   Q. Nothing in this file ever deletes a line from memory.md. Ten thousand
#      runs later, what is that file, and what does reading it cost per run?
#
#   Q. Devika Nair changes teams. Which line of this program notices?
