"""
STEP 8. Failure: one context is doing two jobs, so the 6,000 words the
research phase needed are still sitting there crowding the build phase, which
needed three of them; and the same run has no idea when to give up.

    python3 step8_subagents.py --single-context   one context, both jobs
    python3 step8_subagents.py                    a child does the reading
    python3 step8_subagents.py --runaway          a goal it can never finish

Two pieces land here because they are the same piece seen twice: a budget is
what you give a run, and a sub-agent is a smaller budget you hand to a
narrower job so that a bad one cannot spend yours.
"""

import sys

from harness import (SCRATCH, ContextTooLarge, act, flaky_tool, llm_json, plan,
                     preview, reflect, reset_usage, rule, rupees_used, search_docs,
                     show, tokens_used, validate, write_file)

# ══════════════════════════════════════════════════════════════════════════
#  THE BUDGET: three ceilings and a tripwire, all written before the run
# ══════════════════════════════════════════════════════════════════════════
#
#  In step 2 the budget was iterations, because iterations were the only thing
#  we could count. Now we can count the two things that actually bill.
#
#  Size them against each other or they are decoration. 60,000 tokens at the
#  list price in harness.py is about half a rupee, so these two ceilings sit
#  on top of one another and whichever arrives first is the one that fires.
#  A ceiling that can never fire is not a budget, it is a comment.
#
#  Defend them out loud: half a rupee a run, run once a day for a client, is
#  about 180 rupees a year. Say the number before you say yes to the freedom.

MAX_STEPS = 8            # iterations
MAX_TOKENS = 60_000      # prompt + completion, across the whole run
MAX_COST = 0.50          # rupees, at the list price in harness.py
NO_PROGRESS_AFTER = 3    # identical or failing turns before we call it stuck

TOOLS = {"search_docs": search_docs, "write_file": write_file}
RESEARCH_GOAL = ("Compare three ways to stop duplicate payment retries. Use "
                 "search_docs on at least two different queries, then recommend one.")
BUILD_GOAL = ("Write scratch/decision.md: 5 lines naming the chosen approach, why, "
              "and the facts it rests on.")
BOTH = RESEARCH_GOAL + " Then " + BUILD_GOAL
RUNAWAY_GOAL = "Use flaky_tool to fetch the deploy status, then report the status."

# The shape the parent will accept back from a child, and nothing else.
RESULT_SPEC = {"recommendation": str, "important_facts": list, "sources": list}


def over_budget(step):
    if step >= MAX_STEPS:
        return f"step budget: {MAX_STEPS} iterations"
    if tokens_used() >= MAX_TOKENS:
        return f"token budget: {tokens_used():,} of {MAX_TOKENS:,}"
    if rupees_used() >= MAX_COST:
        return f"cost budget: Rs {rupees_used():.2f} of Rs {MAX_COST:.2f}"
    return None


def no_progress(history):
    """Stuck is not the same as out of budget, and it arrives much earlier.

    No model call here on purpose. Repetition and failure are properties of the
    history you already hold, so detecting them is free. Ask a model "are you
    making progress?" and you have bought one more turn of the thing you are
    trying to stop, from the party least able to see it.
    """
    recent = history[-NO_PROGRESS_AFTER:]
    if len(recent) < NO_PROGRESS_AFTER:
        return None
    calls = {(entry["tool"], str(entry["args"])) for entry in recent}
    if len(calls) == 1:
        return f"the same call {NO_PROGRESS_AFTER} times: {recent[-1]['tool']}"
    if all("error" in str(entry["result"]) for entry in recent):
        return f"{NO_PROGRESS_AFTER} turns, every one an error"
    return None


def loop(goal, tools, max_steps, extra="", tag=""):
    """The step 3 loop with two `if`s added. Returns why it stopped, always."""
    history = []
    try:
        for step in range(max_steps):
            if reason := over_budget(step):
                return None, history, f"STOPPED by {reason}"
            if reason := no_progress(history):
                return None, history, f"STOPPED, no progress: {reason}"

            action = plan(goal, history, tools, extra=extra)
            result = act(action, tools)
            history.append({"step": step + 1, "tool": action.get("tool"),
                            "args": action.get("args") or {}, "result": result})

            rule(f"{tag}ITERATION {step + 1} of {max_steps}")
            show(action, result)
            print(f"  BUDGET   {tokens_used():,}/{MAX_TOKENS:,} tokens · Rs "
                  f"{rupees_used():.2f}/{MAX_COST:.2f} · history "
                  f"~{len(str(history)) // 4:,} tokens")

            reflection = reflect(goal, history, extra=extra)
            print(f"  REFLECT  {preview(reflection)}")
            if reflection.get("answer"):
                return reflection["answer"], history, "finished"
    except ContextTooLarge as wall:
        # A fourth ceiling, which nobody in this file wrote down and somebody
        # else enforces. It ends the run exactly like the three above, and that
        # is the point: the difference between a budget and a wall is only who
        # picked the number.
        return None, history, f"STOPPED by the context limit: {wall}"
    return None, history, f"STOPPED by step budget: {max_steps}"


# ══════════════════════════════════════════════════════════════════════════
#  THE NEW PIECE: a second agent, with its own everything
# ══════════════════════════════════════════════════════════════════════════

def run_subagent(goal, tools, max_steps):
    """A fresh history, a narrow goal, a short tool list, its own step budget.

    The point is not that it is a second brain. It is that its context is a
    different object. Whatever the child reads, thinks and gets wrong stays
    inside it; the parent gets back a dict it declared the shape of in advance.

    Read the return type carefully. This function does not raise. A child that
    fails hands the parent a structured failure, because the parent is running
    a loop and a loop cannot be interrupted by its own helper.
    """
    before = tokens_used()
    rule("SUB-AGENT STARTS: fresh context, its own budget")
    print(f"  goal:  {goal}\n  tools: {list(tools)}\n  budget: {max_steps} steps")

    answer, history, why = loop(goal, tools, max_steps, tag="child ")

    if answer is None:
        return {"ok": False, "error": why, "steps": len(history),
                "tokens": tokens_used() - before}

    try:
        packed = llm_json(
            "Compress this finished research run into a hand-back for the agent "
            "that called you. It has none of your context and never will.\n"
            'Return JSON exactly: {"recommendation":"<one sentence>",'
            '"important_facts":["…","…"],"sources":["…"]}\n'
            "3 facts maximum. Facts only, no prose.\n\n"
            f"GOAL: {goal}\nHISTORY: {history}\n", label="pack")
        result = validate(packed, RESULT_SPEC)
    except ContextTooLarge as error:
        return {"ok": False, "error": f"the child's own hand-back did not fit: {error}",
                "steps": len(history), "tokens": tokens_used() - before}
    except ValueError as error:
        return {"ok": False, "error": f"child returned a malformed result: {error}",
                "steps": len(history), "tokens": tokens_used() - before}

    kept, handed = len(str(history)), len(str(result))
    rule("SUB-AGENT RETURNS")
    print(f"  it READ    ~{kept // 4:,} tokens across {len(history)} turns\n"
          f"  it RETURNS ~{handed // 4:,} tokens: {preview(result, 300)}\n"
          f"  the other {(kept - handed) // 4:,} tokens go with its context, which is\n"
          f"  the entire reason it was a separate agent and not another turn.")
    return {"ok": True, "result": result, "steps": len(history),
            "tokens": tokens_used() - before}


def report(answer, history, why, lesson):
    rule("RESULT")
    print(f"  {answer or why}\n  {len(history)} turns · {tokens_used():,} tokens · "
          f"Rs {rupees_used():.2f} · history ~{len(str(history)) // 4:,} tokens\n")
    print(lesson)


if __name__ == "__main__":
    reset_usage()

    if "--runaway" in sys.argv:
        rule("RUNAWAY: a goal that cannot be met, and a tool that never works")
        print(f"  GOAL: {RUNAWAY_GOAL}")
        report(*loop(RUNAWAY_GOAL, {"flaky_tool": flaky_tool}, MAX_STEPS),
               "  Read which ceiling fired. Not MAX_STEPS, and not the clock.\n"
               "  no_progress() read the history the loop already held, saw the\n"
               "  pattern above, and cost nothing to run. The budget is the\n"
               "  backstop. This is the smoke alarm, and it goes off first.")

    elif "--single-context" in sys.argv:
        rule("SINGLE CONTEXT: one agent, both jobs")
        print(f"  GOAL: {BOTH}")
        report(*loop(BOTH, TOOLS, MAX_STEPS),
               "  Scroll up to the turn that wrote the file and read its in= count.\n"
               "  It re-sent thousands of words of raw research to make a 5 line\n"
               "  decision, and every one of them was a chance to be distracted.")

    else:
        print(f"GOAL: {BOTH}")
        child = run_subagent(RESEARCH_GOAL, {"search_docs": search_docs}, 4)

        # The parent DECIDES. It does not crash, and it does not pretend.
        if child["ok"]:
            handoff = f"RESEARCH HANDED BACK BY A SUB-AGENT:\n{child['result']}\n\n"
            goal = BUILD_GOAL
        else:
            rule("THE CHILD FAILED, AND THE PARENT IS STILL RUNNING")
            print(f"  {child['error']}\n  so the parent chooses what to do about it.")
            handoff = "RESEARCH FAILED. Say so in the file rather than inventing it.\n\n"
            goal = BUILD_GOAL + " The research step failed, so record that instead."

        rule("PARENT RESUMES: its context never saw the research")
        written = (SCRATCH / "decision.md")
        report(*loop(goal, {"write_file": write_file}, 3, extra=handoff),
               (f"  scratch/decision.md: {preview(written.read_text(), 260)}\n"
                if written.exists() else "") +
               "  Compare that history figure with the --single-context one.\n"
               "  Same work, same model, same tools, one fewer thing in the room.")

# ══════════════════════════════════════════════════════════════════════════
# PREDICT before you open step 9
# ══════════════════════════════════════════════════════════════════════════
#
# What does the child return versus what does it keep? What happens to the
# parent if the child errors mid-run? Then: your step 2 budget was sized for a
# three-hop toy. Defend a number for a client's daily unattended task, from a
# budget in rupees. How would you detect no progress without spending a model
# call to ask?
#
# Then, before you move on:
#
#   Q. The child is handed 4 steps. Who picked 4, and what happens to the
#      parent's answer when the honest research needed 6?
#
#   Q. Two children run in parallel and reach opposite recommendations. Which
#      line of this file resolves that? (There isn't one. Write it.)
