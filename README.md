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

**Predict every new abstraction before you read it.**

Every file ends in a `PREDICT` block. Those are not homework and they are not
optional — they *are* the lab. Each one asks the question that makes the next
abstraction necessary, and the next file contains the answer.

Skim straight through and you will have memorised a diagram. Answer the
questions first and you will be able to say, for every box, exactly which
failure comes back if you delete it. That second thing is the point.

---

## The problem

> **What is the NAME of the manager of the person who filed ticket T-1002?**

`data.json` has tickets and employees. Answering takes three hops:

```
get_ticket("T-1002")   -> {filed_by: "E-17"}
get_employee("E-17")   -> {name: "Priya Raman", manager: "E-04"}
get_employee("E-04")   -> {name: "Devika Nair"}          <- the answer
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
pip install requests
```

**2 · Pick a provider**

*Groq (fast, needs a free key):*

```bash
export GROQ_API_KEY=gsk_...        # free: https://console.groq.com/keys
```

*Ollama (no key, runs offline):*

```bash
export PROVIDER=ollama
ollama pull qwen3.5:9b
```

**3 · Check it works**

```bash
python3 step1_one_shot.py
```

It prints its provider and model on the first line. If that works, you are set.

### Choosing a model

| Provider | Default | Notes |
|---|---|---|
| `groq` | `openai/gpt-oss-20b` | Whole lab runs in well under a minute. |
| `ollama` | `qwen3.5:9b` | ~15s per call, so step 3 takes about 3 minutes. |

Override either with `export MODEL=...`.

**Do not use a 3B model for this lab.** We tested `llama3.2:3b`: it plans the
first hop perfectly, then fails 0/5 at planning hop 3, and — worse — it
*always* claims an answer even when the data isn't there yet. It would confidently
stop on iteration 1 with the wrong name. That failure is itself a great
discussion (see Experiment 4), but it is a bad way to meet the loop.

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

**`step2_loop.py`** — The **stopping condition** (before the freedom, not after
the bill), the **loop**, **state**, and the **tool registry**. Part 1 runs a loop
with no memory: three identical iterations. That is repetition, not iteration.
Part 2 adds a list, and the program walks the chain by itself. Then it keeps
going, tries to call a tool named `none` to signal it's finished, fails, and
burns the rest of the budget — because nothing in it can judge a result or end a
run.

**`step3_agent.py`** — **OBSERVE** and **REFLECT**, and the loop closes. Now it
stops in three iterations because something decided it was done, not because a
counter ran out. Only here do the five boxes get their names.

</details>

---

## What to watch for when step 3 runs

Two things worth pausing on, both visible in a normal run:

**The model tries to say "I'm done" through a channel that doesn't exist.**
In step 2, watch for `none({}) -> no such tool 'none'`. It has the answer and no
way to tell you. Every field in your contract is a permission to communicate.

**OBSERVE and REFLECT can disagree — and REFLECT should win.** On the last
iteration you will often see OBSERVE misread the result (`"the manager is
E-01… name still unknown"`) while REFLECT returns `Devika Nair` correctly.
That is not luck. `reflect()` receives `history` — the raw evidence — while
OBSERVE only ever sees one step. A step that decides whether you are finished
cannot do that job on a paraphrase.

That single design decision is the difference between an agent that terminates
and one that spins until the budget dies. Experiment 2 makes you break it
on purpose.

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
4. **The weak model** — `PROVIDER=ollama MODEL=llama3.2:3b python3 step3_agent.py`.
   It will answer confidently and wrongly. Which box failed? Could a better
   prompt have saved it, or is this a capability floor? How would you *detect*
   this in production, given it never errors?

Then, before the next session:

5. Swap the two tools for a tool from **your** capstone domain. Change nothing
   else — not the loop, not the five functions. If the loop doesn't survive the
   swap, that tells you something about the loop.
6. Write your stopping condition first, and defend the number from a budget.

---

## What's in the box

```
README.md            this file
data.json            tickets and employees. no network required.

step1_one_shot.py    the program with no loop  (also holds the givens:
                       llm, llm_json, and the two tools)
step2_loop.py        budget, loop, state, tool registry
step3_agent.py       observe, reflect, and the name of the thing you built
```

`step1_one_shot.py` holds the plumbing — the provider switch, the two LLM
helpers, the data loading — and steps 2 and 3 import from it. That is on
purpose: **the givens never change across the three files.** The only thing
that changes is the control flow.

Both providers speak the same OpenAI-shaped API, so there is one code path and
one `requests` call for both. No SDK. There is no framework in this repository,
and that is the point.

---

## If something goes wrong

| Symptom | Fix |
|---|---|
| `No GROQ_API_KEY set` | `export GROQ_API_KEY=gsk_...`, or `export PROVIDER=ollama` |
| `groq returned 404 ... model does not exist` | That model was retired. `export MODEL=openai/gpt-oss-20b` |
| `(rate limited, waiting 7s)` | Normal on a free key. It retries itself; just wait. |
| `(model emitted invalid JSON, retrying)` | Normal. Strict JSON mode occasionally rejects the model's own output. |
| Connection refused on `PROVIDER=ollama` | Ollama isn't running. Start it, then `ollama pull qwen3.5:9b`. |
| Agent never finishes / answers nonsense | Your model is too small. See *Choosing a model*. |
| `ModuleNotFoundError: step1_one_shot` | Run from the repo root, not from another directory. |
