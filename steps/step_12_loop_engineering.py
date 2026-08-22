"""
STEP 12 — Closing: the labels come off, and loop engineering begins
══════════════════════════════════════════════════════════════════

    python steps/step_12_loop_engineering.py

Prints tonight's closing challenge and the map of what we study next.
Nothing here calls an API. This is the part you argue about.
"""

from lab import rule

rule("CLOSING CHALLENGE — the labels are gone. Name every line.")

print(
    """
    for step in range(MAX_STEPS):

        x = llm(...)          #  ?
        y = llm(...)          #  ?
        z = tool(...)         #  ?
        a = llm(...)          #  ?
        b = llm(...)          #  ?

        if b["done"]:         #  ?
            return b["answer"]

    Which one is deterministic? Which one can end the run? Which one is the
    only line that touches the world? Which one, if you deleted it, would turn
    this back into last week's program?
"""
)

rule("IF I GIVE THIS EXACT AGENT TO TEN TEAMS, DO ALL TEN PERFORM EQUALLY?")

print(
    """
No. The loop is not the hard part any more. The decisions inside and around
each box are. That is loop engineering, and it is the rest of this module.

  SENSE     What context gets loaded? What gets left out? How is history
            compacted once it stops fitting?
  PLAN      How much planning? When may a plan change? How do you verify a
            plan before paying for the actions in it?
  ACT       Which tools exist at all? What permissions? What schemas? What
            happens on failure — retry, escalate, or stop?
  OBSERVE   What counts as success? What is extracted from a raw result, and
            what is thrown away?
  REFLECT   Who evaluates? Against what threshold? What triggers a replan?
            What is allowed to enter memory?
  STOP      Iterations? Money? Time? Wall-clock? A milestone condition?
"""
)

rule("THREE EXPERIMENTS — do these now, one line each, in step_11")

print(
    """
  1. STOP.    Change the goal back to 10 years (2016-2025) and leave
              MAX_STEPS = 8. Run it. Does it stop cleanly or claim a false
              answer? Whose fault is the outcome — the model's or yours?

  2. SENSE.   In sense(), delete `history` from the prompt but keep appending
              to it. The memory still exists; nothing reads it. Predict the
              behaviour before you run it, then run it.

  3. REFLECT. Delete the `if reflection["done"]` branch. The reflection is
              still computed, still printed, and now decides nothing.
              What species of software is this now?
"""
)

rule("THE SDK REVEAL")

print(
    """
    agent = Agent(model=model, tools=tools, instructions=instructions)
    result = agent.run(goal)

  Q. What disappeared?
       history · the loop · tool dispatch · structured outputs · iteration
       handling · the stopping condition · context management

  Q. Did the LOOP disappear?
       No. We stopped writing it. That is what an abstraction is.

  An Agent SDK is not a different species of software. It packages the exact
  decisions you just made by hand.

  Q. When is an abstraction useful?
  Q. When does it become dangerous?
       → when you no longer understand the assumptions it is hiding.
"""
)

rule("AND THE CODING AGENTS YOU USE EVERY DAY")

print(
    """
    Ours                       Claude Code / Codex
    ─────────────────          ─────────────────────────────────
    LLM                        LLM
    1 weather tool             shell, filesystem, search, editor,
    a Python list                tests, git
    5 iterations               memory, permissions, compaction,
                                 approval, verification, the loop

  Zoom into any ten seconds of Codex working. What files exist? What did the
  user ask? What failed? What did the test say? → it senses. It plans. It
  edits. It runs something. It reads the terminal → it observes. It reflects.
  Then it does something else.

  Same shape. Much better engineering. That is exactly why we learned the
  primitive before the product: new agent products become things you can
  reverse-engineer instead of things you have to trust.
"""
)

rule("LAST SESSION I ASKED")

print(
    """
  "What did we give the LLM that turned it into an agent?"

  Tonight you wrote the answer. Not another model. Not another tool. Not
  another API. We gave it a mechanism for experiencing the consequence of one
  decision and using that consequence to make the next decision.

  That mechanism is the loop. Agency is the abstraction; the loop is the
  implementation. Remove it and you are looking at an LLM with tools, which
  is what you had last week.

  From here the question changes. We know how to build an agent.
  Now we learn how to engineer the loop.
"""
)

rule("BEFORE THE NEXT SESSION")

print(
    """
  1. Run all three experiments above and bring what broke.
  2. Swap the weather tools for a tool from YOUR capstone domain. Change
     nothing else — not the loop, not the five functions. If the loop does
     not survive the swap, that tells you something about the loop.
  3. Write your stopping condition first, and defend the number from a budget.
  4. List ten decisions you currently make by hand and split them with the
     delegation test: verifiable goes to the agent, unverifiable stays with
     you. Bring the split — it is raw material for capstone scoping.
"""
)
