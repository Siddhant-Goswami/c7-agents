# Building the Agent Loop From First Principles

**100xEngineers · Module 3 · Hands-on lab**

Three files. About twenty minutes. No framework, no vendor, no folders.

---

## What this is

You already know how to call an LLM and how to call a tool. This lab adds
almost nothing to that. It starts with the program you can already write:

```python
ticket = get_ticket("T-1002")
answer = llm(f"{question}\n\n{ticket}")
```

and ends with a working agent. Between those two points, every piece is
something you already have — what changes is the **order** the pieces run in,
and the fact that they now **repeat**.

The whole lab answers one question:

> **What is the minimum we must add so that the *software*, rather than the
> *human*, decides what happens next?**

### The one rule

**Work out every new piece before you read it.**

Every file ends in a `PREDICT` block. Those are not homework and they are not
optional — they *are* the lab. Each one asks the question that makes the next
piece necessary, and the next file contains the answer.

Skim straight through and you will have memorised a diagram. Answer the
questions first and you will be able to say, for every part of an agent,
exactly which failure comes back if you delete it. That second thing is the
point.

---

## The problem

Imagine any place where people report problems — an office, a college, a
hospital. When something breaks, somebody writes it down. That written-down
complaint is called a **ticket**: a short note with an ID like `T-1002`, a
description of what went wrong, and a record of who reported it.

Our `data.json` keeps two separate lists, the way a real system would:

- **Tickets** — each one says what the problem is and *who reported it*.
- **People** — each person has a name, a team, and a **manager**: the person
  they report to.

The catch is that these lists don't refer to people by name. They use ID
codes, like a roll number: `E-17`, `E-04`. A ticket tells you it was reported
by `E-17` and nothing more. To find out that `E-17` is a person called Priya,
you have to go look up `E-17` in the list of people. And Priya's record won't
name her manager either — it just says her manager is `E-04`. To get *that*
name, you look up `E-04`.

So this question:

> **What is the NAME of the manager of the person who filed ticket T-1002?**

can only be answered in three separate lookups, each one handing you the code
you need for the next:

```
get_ticket("T-1002")   -> {filed_by: "E-17"}                  who reported it
get_employee("E-17")   -> {name: "Priya Raman", manager: "E-04"}   her manager's code
get_employee("E-04")   -> {name: "Devika Nair"}               <- the answer
```

It is deliberately tiny, and it is chosen for one property:

**You cannot write hop 2 until hop 1 has returned.** The argument to the next
call is inside the previous result. So no amount of planning ahead saves you —
the sequence is not knowable in advance, by us or by anyone. That is the
smallest possible problem that a loop is genuinely *required* for.

No network, no API key for the data, no waiting. The interesting part is the
control flow, not the domain.

---

## Setup

**1 · Install the one dependency**

```bash
pip install groq
```

**2 · Add your API key**

```bash
export GROQ_API_KEY=gsk_...        # free key: https://console.groq.com/keys
```

**3 · Check it works**

```bash
python3 step1_one_shot.py
```

It prints the model it is using on the first line. If that works, you are set.
The whole lab then runs in well under a minute.

The default model is `openai/gpt-oss-20b`. If it is ever retired, swap it with
`export MODEL=...` and nothing else changes.

---

## The three steps

Run them in order. Read the docstring at the top, run the file, then answer
the `PREDICT` block at the bottom *before* opening the next one.

| # | File | The question you answer |
|---|------|------------------------|
| 1 | `step1_one_shot.py` | Who decides what happens next? |
| 2 | `step2_loop.py` | What does a second attempt need in order to differ from the first? |
| 3 | `step3_agent.py` | Who decides whether we stop or go again? |

<details>
<summary><b>Spoilers</b> — what each file adds. Open only if you are stuck.</summary>

<br>

**`step1_one_shot.py`** — Attempt A makes one tool call and cannot answer.
Attempt B hardcodes all three hops and *works* — then the same code, pointed at
ticket `T-1007`, produces garbage, because that chain is two hops long and the
program has no way to notice. Every correct thing about Attempt B was knowledge
*we* typed into the source.

**`step2_loop.py`** — Four things: a **stopping condition** (written before you
grant the freedom, not after the bill arrives), the **loop**, a **memory**, and
a **list of tools the model is allowed to name**. Part 1 runs a loop with no
memory and produces three identical turns — that is repetition, not progress.
Part 2 adds one Python list, and the program walks the three hops by itself,
without us typing them. Then it keeps going, tries to call a tool named `none`
to signal that it's finished, fails, and burns the rest of its budget — because
nothing in it can judge a result or end a run.

**`step3_agent.py`** — **OBSERVE** and **REFLECT**, and the loop closes. Now it
stops in three iterations because something decided it was done, not because a
counter ran out. Only here do the five boxes get their names.

</details>

---

## What to watch for when step 3 runs

Two things worth pausing on, both visible in a normal run:

**The model tries to say "I'm done" and has no way to say it.** In step 2, watch
for `none({}) -> no such tool 'none'`. It has worked the answer out, and the only
thing it is allowed to reply with is a tool call — so it invents a fake tool
called `none`. It is not confused; we simply never gave it a way to say
"finished". Whatever you let a model reply with is the only thing it can tell you.

**Two steps can disagree, and the one with better information should win.** On
the last iteration you will often see OBSERVE misread the result (`"the manager
is E-01… name still unknown"`) while REFLECT answers `Devika Nair` correctly.
That is not luck. `reflect()` is handed `history` — everything that actually
happened — while OBSERVE only ever sees the single most recent step. The step
that decides whether you are finished should look at the real evidence, not at
somebody else's summary of it.

That one decision is the difference between an agent that stops and an agent
that spins until its budget runs out. Experiment 2 makes you break it on purpose.

---

## Experiments

The first three are in the comments at the bottom of `step3_agent.py`; each is
one line.

1. **STOP** — set `max_steps=2`. Does it stop cleanly, or claim a false answer?
   Whose fault is that outcome, the model's or yours?
2. **SENSE** — pass `situation` to `plan()` and `reflect()` instead of `history`.
   The memory still exists; nothing reads it raw. Predict what breaks first.
3. **REFLECT** — delete the `if reflection.get("answer")` branch. Reflection is
   still computed, still printed, and now decides nothing. What species of
   software is this now?

Then, before the next session:

4. Swap the two tools for a tool from **your** capstone domain. Change nothing
   else — not the loop, not the five functions. If the loop doesn't survive the
   swap, that tells you something about the loop.
5. Write your stopping condition first, and defend the number from a budget.

---

## What's in the box

```
README.md            this file
data.json            tickets and employees. no network required.

step1_one_shot.py    the program with no loop
step2_loop.py        the stopping condition, the loop, and memory
step3_agent.py       the two steps that finish the loop, and what it's called
```

`step1_one_shot.py` also holds the shared plumbing: the two functions that talk
to the model and the two that read `data.json`. Steps 2 and 3 import all of it
from there rather than redefining it.

That is on purpose. **The tools and the model never change across the three
files.** The only thing that changes is the order things run in, and whether
they repeat. If the agent in step 3 feels smarter than the program in step 1,
it isn't — it is the same model and the same two tools, wired differently.

The only library here is Groq's own client, which just sends the request and
retries when you hit a rate limit. There is no agent framework anywhere in this
repository, and that is the point: everything in step 3 is code you wrote.

---

## If something goes wrong

| Symptom | Fix |
|---|---|
| `The api_key client option must be set` | `export GROQ_API_KEY=gsk_...` |
| `model does not exist or you do not have access` | That model was retired. Pick a live one from <https://console.groq.com/docs/models> and `export MODEL=...` |
| A run pauses for a few seconds | A rate limit on the free key. The client waits and retries by itself. |
| `The model failed to return valid JSON three times` | Rare. Re-run it. |
| `ModuleNotFoundError: groq` | `pip install groq` |
| `ModuleNotFoundError: step1_one_shot` | Run from the repo root, not from another directory. |
