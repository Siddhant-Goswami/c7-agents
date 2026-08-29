"""
STEP 5. Failure: the process dies at iteration 3 of 8, and every hop it had
already paid for dies with it, because the only copy lived in a Python list.

    python3 step5_persistence.py --kill-at 2      then run it again
    python3 step5_persistence.py --fresh          forget everything, start over

Nothing here is clever. It is one json.dump per iteration. The thinking is
entirely in deciding WHAT to write, and this file is really about that:

    STATE    what is true now.        Survives the process. This file.
    HISTORY  what happened this run.  Dies with the process, and should.
    MEMORY   what survives across runs, on purpose. That is step 7.

Get those three confused and you either resume into a lie or resume into
nothing at all.
"""

import json
import sys

from harness import (SCRATCH, TICKET_TOOLS, act, plan, preview, reflect, rule,
                     show, write_file)

MAX_STEPS = 6
STATE_FILE = SCRATCH / "state.json"

TOOLS = {**TICKET_TOOLS, "write_file": write_file}
GOAL = ("Find the NAME of the manager of the person who filed ticket T-1002, "
        "then save that name to scratch/answer.md.")


# ══════════════════════════════════════════════════════════════════════════
#  THE NEW PIECE: two functions and a file
# ══════════════════════════════════════════════════════════════════════════

def save_state(goal, status, steps, iterations):
    """Write what is TRUE, not what was SAID.

    Look at what goes in: the calls that were made and the values that came
    back. Look at what does not: the model's thought on each turn, the
    reflection JSON, the plans it considered and dropped. Those are the record
    of one run's reasoning. They are useful while the run is alive and they are
    noise, or worse, to the run that picks this up tomorrow. A resumed agent
    that inherits yesterday's half-formed theory will defend it.
    """
    STATE_FILE.write_text(json.dumps({
        "goal": goal,
        "status": status,
        "iterations_used": iterations,
        "completed_steps": steps,
    }, indent=2))


def load_state(goal):
    """Resume only if the saved state is about the goal in front of us.

    That `if` is the whole safety property. A state file keyed on nothing will
    happily hand a run about ticket T-1002 the half-finished work of a run
    about last week's payroll, and the agent will not notice.
    """
    if not STATE_FILE.exists():
        return None
    saved = json.loads(STATE_FILE.read_text())
    return saved if saved.get("goal") == goal else None


def run(goal, kill_at=None):
    saved = load_state(goal)

    if saved and saved["status"] == "done":
        rule("ALREADY DONE")
        print(f"  scratch/state.json says this goal finished in "
              f"{saved['iterations_used']} iterations.\n"
              f"  Re-run with --fresh to make it forget and do the work again.")
        return None, 0

    if saved:
        steps = saved["completed_steps"]
        rule("RESUMING FROM scratch/state.json")
        print(f"  a previous run got {len(steps)} steps in and then stopped.")
        for entry in steps:
            print(f"    step {entry['step']}: {entry['tool']}({entry['args']}) "
                  f"-> {preview(entry['result'], 60)}")
        print("  those calls will NOT be paid for again.")
    else:
        steps = []
        rule("COLD START: no usable state for this goal")

    # HISTORY is rebuilt from STATE, and it is smaller than it was, because the
    # thoughts and reflections did not survive. That is the design, not a bug.
    history = list(steps)

    for step in range(len(steps), MAX_STEPS):
        action = plan(goal, history, TOOLS)
        result = act(action, TOOLS)
        entry = {"step": step + 1, "tool": action.get("tool"),
                 "args": action.get("args") or {}, "result": result}
        history.append(entry)

        rule(f"ITERATION {step + 1} of {MAX_STEPS}")
        show(action, result)

        reflection = reflect(goal, history)
        print(f"  REFLECT  {preview(reflection)}")
        done = bool(reflection.get("answer"))

        # Save AFTER the world was touched and BEFORE anything else can go
        # wrong. Save before the act and you will resume believing you did
        # something you did not do.
        save_state(goal, "done" if done else "in_progress", history, step + 1)
        print(f"  SAVED    scratch/state.json  ({len(history)} completed steps, "
              f"status={'done' if done else 'in_progress'})")

        if done:
            return reflection["answer"], step + 1

        if kill_at and step + 1 == kill_at:
            rule(f"KILLED AT ITERATION {kill_at}")
            print("  Pretend this was Ctrl-C, an OOM kill, or a laptop lid.\n"
                  "  Everything in the Python process is gone as of this line.\n\n"
                  "  Now run the same command again WITHOUT --kill-at.")
            sys.exit(0)

    return None, MAX_STEPS


if __name__ == "__main__":
    if "--fresh" in sys.argv:
        STATE_FILE.unlink(missing_ok=True)
        print("scratch/state.json deleted.\n")

    kill_at = None
    if "--kill-at" in sys.argv:
        kill_at = int(sys.argv[sys.argv.index("--kill-at") + 1])

    print(f"GOAL: {GOAL}")
    answer, used = run(GOAL, kill_at)

    rule("RESULT")
    if answer:
        print(f"  {answer}   (this run used {used} iterations)")
        print(f"  scratch/answer.md: "
              f"{preview((SCRATCH / 'answer.md').read_text() if (SCRATCH / 'answer.md').exists() else 'not written')}")


# ══════════════════════════════════════════════════════════════════════════
# PREDICT before you open step 6
# ══════════════════════════════════════════════════════════════════════════
#
# Kill it at iteration two, restart. What resumed and what did not? Which line
# of the state file made the difference? Name one thing in history that
# deliberately did not survive, and why that is correct.
#
# Then, before you move on:
#
#   Q. The agent wrote scratch/answer.md at iteration 4 and the process died at
#      iteration 5. State says the write happened. Is that true? Name the
#      window where the file and the state file disagree, and what a real
#      system does about it.
#
#   Q. You resume a run from yesterday. The ticket was reassigned overnight.
#      Which of the two is now wrong: the state, or the world?
