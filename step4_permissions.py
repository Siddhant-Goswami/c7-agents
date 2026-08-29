"""
STEP 4. Failure: the agent has too much authority, and nothing stands between
its next plausible idea and your filesystem.

    python3 step4_permissions.py

Part 1 of this repo ended with a working agent. Everything from here on is
what happens when you point that agent at a real machine instead of a
read-only dict, and each file is named after the failure that made it exist.

The agent below is the step 3 agent. Same model, same loop. The only change
is the toolbox: it can now read files, write files, and run shell commands.
Watch what a legitimate goal does with that.
"""

import sys

from harness import (FILE_TOOLS, SCRATCH, act, ask_yes_no, inside_scratch, plan,
                     preview, reflect, reset_usage, rule, show)

MAX_STEPS = 4

# The goal is honest, ordinary, and the kind of thing anybody would type. Read
# it and notice there is nothing wrong with it.
GOAL = ("Read scratch/notes.md, summarise it in three short lines, and save the "
        "summary to scratch/notes.md so the file holds the summary.")

NOTES = """Incident notes, payments team, 14 March.
Checkout retried the same charge four times for 312 customers.
Root cause: the idempotency key was rebuilt per attempt instead of per order.
Refunds issued the same evening by Priya Raman; total 4.1 lakh.
Devika Nair signed off the fix. Regression test added: test_idempotency_key.
Open question: the vendor still shows 11 unreconciled settlements.
Do not lose this file. It is the only record of the 11 open settlements.
"""


def seed_scratch():
    """Put the file back the way it was, so the demo starts identical each time."""
    (SCRATCH / "notes.md").write_text(NOTES)


# ══════════════════════════════════════════════════════════════════════════
#  THE NEW PIECE: one function, called before the world is touched
# ══════════════════════════════════════════════════════════════════════════

# read_file is not on this list. Reading inside scratch/ is reversible, and a
# gate you are asked to clear forty times is a gate you stop reading. Gate the
# action classes that cannot be undone, and let the rest through.
SENSITIVE = {"bash", "write_file"}


def permission_gate(tool_name, args):
    """Show the human exactly what is about to happen, and require a yes.

    Note where this sits: BETWEEN plan() and act(). Not inside the prompt.
    A rule written in the prompt is a request; the model complies with it most
    of the time, which is another way of saying it does not comply with it.
    This is an `if` statement in your code, and it holds every time.
    """
    if tool_name not in SENSITIVE:
        return True

    rule("PERMISSION REQUIRED")
    print(f"  the agent wants to run:  {tool_name}")
    for key, value in (args or {}).items():
        print(f"     {key} = {preview(value, 160)}")
    if tool_name == "write_file":
        target = inside_scratch(args.get("path", ""))
        if target and target.exists():
            print(f"  NOTE: {target.name} already exists, {target.stat().st_size} bytes. "
                  f"This overwrites it, and there is no undo.")
    return ask_yes_no("  allow?")


def run(goal, gated, max_steps=MAX_STEPS):
    history = []
    for step in range(max_steps):
        action = plan(goal, history, FILE_TOOLS)
        name, args = action.get("tool"), action.get("args") or {}

        if gated and not permission_gate(name, args):
            # Denial is a RESULT, not a crash. The agent is told no in the same
            # channel it hears everything else, so it can go and do something
            # legal instead. A gate that kills the run teaches the agent nothing.
            result = {"error": "permission denied by user"}
        else:
            result = act(action, FILE_TOOLS)

        history.append({"step": step + 1, "tool": name, "args": args, "result": result})

        rule(f"ITERATION {step + 1} of {max_steps}")
        show(action, result)

        reflection = reflect(goal, history)
        print(f"  REFLECT  {preview(reflection)}")
        if reflection.get("answer"):
            return reflection["answer"], step + 1
    return None, max_steps


if __name__ == "__main__":
    print(f"GOAL: {GOAL}")

    # ─── PART 1 ─── the agent from step 3, with a filesystem ──────────────
    rule("PART 1: no gate. The agent has the authority we gave it.")
    seed_scratch()
    print(f"  scratch/notes.md before:  {len(NOTES)} bytes, "
          f"last line = {NOTES.strip().splitlines()[-1]!r}")
    reset_usage()
    run(GOAL, gated=False)

    after = (SCRATCH / "notes.md").read_text()
    rule("WHAT IS IN THE FILE NOW")
    print(f"  {preview(after, 400)}")
    print(f"\n  {len(NOTES)} bytes went in. {len(after)} bytes are there now.")
    if len(after) < len(NOTES):
        print("  The 11 unreconciled settlements are gone. Nothing asked us first.\n"
              "  The agent did not malfunction. It did exactly what the goal said,\n"
              "  and the goal was written by a human who had not thought it through.")
    else:
        print("  This run happened not to destroy it. Run it again and it will.\n"
              "  'Usually safe' is the property we are about to stop relying on.")

    print("\n  Nothing above is a model problem, so no model fixes it.\n"
          "  The missing thing is not intelligence. It is an interlock.")

    # ─── PART 2 ─── the same run, with one function in the way ────────────
    rule("PART 2: the same goal, same model, with permission_gate()")
    seed_scratch()
    print("  scratch/notes.md restored. Answer n at the prompt and watch what\n"
          "  the agent does with the refusal.\n")
    reset_usage()
    answer, used = run(GOAL, gated=True)

    rule("RESULT")
    print(f"  {answer or 'no answer'}   (in {used} iterations)")
    print(f"  scratch/notes.md is now {len((SCRATCH / 'notes.md').read_text())} bytes.")
    print("\n  You did not make the agent safer. You made yourself present at the\n"
          "  one moment that could not be undone. That is the entire mechanism.")
    sys.exit(0)


# ══════════════════════════════════════════════════════════════════════════
# PREDICT before you open step 5
# ══════════════════════════════════════════════════════════════════════════
#
# Before the run: name the worst thing this agent can now do in pursuit of a
# legitimate goal. After: which of the three tools is irreversible, and what
# does that imply about which action classes need a gate? Who decides that,
# the model or you?
#
# Then, before you move on:
#
#   Q. The gate above asks about a TOOL. Real ones ask about an ACTION:
#      the same write_file is fine into scratch/draft.md and not fine over
#      scratch/notes.md. What would you have to pass permission_gate() for it
#      to tell those two apart?
#
#   Q. Your agent runs unattended at 3am. There is no terminal to answer y/n.
#      What replaces the human, and what does the gate become?
