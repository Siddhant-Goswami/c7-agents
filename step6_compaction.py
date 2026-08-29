"""
STEP 6. Failure: context grows forever, so a run that is going well gets
slower and more expensive every turn and then hits a wall it cannot see.

    python3 step6_compaction.py --no-compact     watch the tokens climb
    python3 step6_compaction.py                  watch them stop climbing

Run the first command and read only one column: the in= number on each
[tokens] line. Nothing is wrong. The agent is working. That climb IS the
work, because every turn re-sends every previous turn.
"""

import sys

from harness import (SCRATCH, ContextTooLarge, act, llm, plan, preview, reflect,
                     reset_usage, rule, search_docs, show, write_file)

MAX_STEPS = 6
TOOLS = {"search_docs": search_docs, "write_file": write_file}

GOAL = ("Research why duplicate payment retries happen. Call search_docs at least "
        "three times with DIFFERENT queries (for example idempotency keys, retry "
        "backoff, settlement reconciliation), then write a 5 line brief to "
        "scratch/brief.md citing what you searched.")

# Two numbers, and both are judgement calls you have to defend.
COMPACT_AT = 6000    # estimated tokens of history above which we compact
KEEP_RECENT = 2      # turns kept word for word, never summarised


def size_of(history):
    """Roughly four characters to a token. Close enough to make a decision on,
    and it costs nothing, which matters because we check it every turn."""
    return len(str(history)) // 4


# ══════════════════════════════════════════════════════════════════════════
#  THE NEW PIECE: one function that trades detail for room
# ══════════════════════════════════════════════════════════════════════════

def compact_history(goal, history):
    """Replace everything older than the last few turns with a summary.

    Three decisions are visible here, and they are the whole of it:

      the GOAL is never compacted        it is what the summary is FOR
      the last KEEP_RECENT turns are     the next plan() depends on them in
        kept word for word                 detail, and paraphrase breaks that
      everything before that becomes     one model call, and a lossy one

    Be clear-eyed about the third line. This is not compression. It is a
    lossy summary written by the same model whose reasoning depends on it,
    and it will drop something. Your job is to choose WHICH somethings are
    droppable, which is what the prompt below is really doing.
    """
    if len(history) <= KEEP_RECENT or size_of(history) < COMPACT_AT:
        return history, None

    old, recent = history[:-KEEP_RECENT], history[-KEEP_RECENT:]
    before = size_of(history)

    summary = llm(
        "Summarise these completed agent steps for a run that is still going.\n"
        "You MUST preserve, exactly:\n"
        "  1. every tool call already made, with its arguments, so they are not repeated\n"
        "  2. every concrete finding that bears on the GOAL\n"
        "  3. anything that failed, and how\n"
        "Drop prose, filler and repetition. 8 lines maximum.\n\n"
        f"GOAL: {goal}\n"
        f"STEPS: {old}\n",
        label="compact",
    )

    compacted = [{"step": "1-%d" % len(old), "tool": "SUMMARY OF EARLIER STEPS",
                  "args": {}, "result": summary}] + recent
    after = size_of(compacted)

    rule("COMPACTION")
    print(f"  {len(old)} old turn{'s' if len(old) != 1 else ''} became 1 summary.")
    print(f"  history: ~{before:,} tokens  ->  ~{after:,} tokens "
          f"({100 - after * 100 // max(before, 1)}% smaller)")
    print(f"  the summary, in full:\n    {preview(summary, 600)}")
    return compacted, before - after


def run(goal, compact):
    try:
        return attempt(goal, compact)
    except ContextTooLarge as wall:
        # Not a crash and not a bug. The run asked for more room than it is
        # allowed and there is no retry that fixes it. On a paid key this is
        # the context window; on a free one it is the per-minute cap. Both
        # arrive exactly here, and both have the same cure.
        rule("THE WALL")
        print(f"  {wall}\n")
        print("  That is the end of the run. Not slower: over.\n"
              "  Nothing was wrong with the goal, the tools, or the model.\n"
              "  The run simply kept every word it had ever read and re-sent\n"
              "  all of it, one more time, until it was not allowed to.")
        return None, 0, 0


def attempt(goal, compact):
    history, saved = [], 0
    for step in range(MAX_STEPS):
        action = plan(goal, history, TOOLS)
        result = act(action, TOOLS)
        history.append({"step": step + 1, "tool": action.get("tool"),
                        "args": action.get("args") or {}, "result": result})

        rule(f"ITERATION {step + 1} of {MAX_STEPS}")
        show(action, result)

        # Compact the moment the history grew, not on the way into the next
        # turn. One turn of delay means reflect() still sees the full result
        # that has just landed on top of everything else, which is the exact
        # call that does not fit.
        if compact:
            history, freed = compact_history(goal, history)
            saved += freed or 0
        turns = f"{len(history)} turn" + ("s" if len(history) != 1 else "")
        print(f"  HISTORY  {turns}, about {size_of(history):,} tokens")

        reflection = reflect(goal, history)
        print(f"  REFLECT  {preview(reflection)}")
        if reflection.get("answer"):
            return reflection["answer"], step + 1, saved
    return None, MAX_STEPS, saved


if __name__ == "__main__":
    compact = "--no-compact" not in sys.argv
    print(f"GOAL: {GOAL}")
    rule("COMPACTION ON" if compact else "COMPACTION OFF: the raw run")
    if not compact:
        print("  Read the in= column on the [tokens] lines and nothing else.\n"
              "  Every turn re-sends every turn before it. search_docs returns\n"
              "  2,000 words per call, so the growth is not subtle.\n")

    reset_usage()
    answer, used, saved = run(GOAL, compact)

    rule("RESULT")
    print(f"  {answer or 'no answer'}   (in {used} iterations)")
    if not compact and used == 0:
        print("  Now run it again without --no-compact and watch the same goal\n"
              "  finish, because compact_history() stops it re-sending the past.")
    if (SCRATCH / "brief.md").exists():
        print(f"  scratch/brief.md: {preview((SCRATCH / 'brief.md').read_text(), 200)}")
    if compact:
        print(f"\n  Compaction removed about {saved:,} tokens of prompt that would\n"
              "  otherwise have been re-sent on every remaining turn.")
        print("  Now go and read what the summary threw away, and ask whether\n"
              "  this particular run happened to need it.")
    else:
        print("\n  Nothing failed here. That is what makes it dangerous: the run\n"
              "  gets more expensive every turn and reports success the whole way,\n"
              "  right up to the turn where the window is full and it does not.")


# ══════════════════════════════════════════════════════════════════════════
# PREDICT before you open step 7
# ══════════════════════════════════════════════════════════════════════════
#
# Run the same goal with compaction off, then on. What information did the
# summary lose, and did the run notice? Name one task where the loss would
# have been fatal.
#
# Then, before you move on:
#
#   Q. Compaction is a model call summarising a model's own work, and its
#      output is trusted by the next turn without review. Where else in this
#      repo does an unreviewed model output get treated as fact, and which of
#      those would you gate?
#
#   Q. KEEP_RECENT = 2. Defend 2. What breaks at 1, and what does 8 cost you?
