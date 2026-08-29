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

---

## Part 2: Build the Harness

Part 1 ended with a working agent: five functions and a stopping condition.
Part 2 does not add a sixth function to it. It takes that same agent, points
it at a real machine, breaks it six times, and derives one piece of the
harness from each break.

Same rule as before, and it matters more here, because every failure below is
one you will meet in production and only some of them announce themselves:

> **Run the file, watch the failure, and write your answer to the `PREDICT`
> block before you read the fix.**

The agent does not get smarter anywhere in Part 2. The model never changes,
and the tools barely do. What changes is what surrounds the loop.

**One amendment to the dependency claim above:** the only libraries in this
repo are the Groq client, plus the OpenAI Agents SDK for `step9_sdk.py` only,
which is the one file whose entire point is that somebody else wrote it.

### The six steps

| # | File | The question you answer |
|---|------|------------------------|
| 4 | `step4_permissions.py` | What stands between the agent's next reasonable idea and your filesystem? |
| 5 | `step5_persistence.py` | The process just died. What survived, and what should have? |
| 6 | `step6_compaction.py` | The context will not fit. What do you throw away, and who notices? |
| 7 | `step7_memory.py` | What should the agent still know tomorrow, and what must it forget? |
| 8 | `step8_subagents.py` | One context is doing two jobs. And how does a run know it is stuck? |
| 9 | `step9_sdk.py` | Which line of the code you just wrote does each SDK noun replace? |

<details>
<summary><b>Spoilers</b> for Part 2, what each file adds. Open only if you are stuck.</summary>

<br>

**`step4_permissions.py`** adds `permission_gate()`. The agent gets `bash`,
`read_file` and `write_file`, and an ordinary goal ("summarise this file and
save the summary over it") destroys the only copy of something. Nothing
malfunctioned. The gate goes between `plan()` and `act()`, not in the prompt,
because a rule in a prompt is a request and an `if` statement is not. Denial
comes back to the agent as a tool result, so it can adapt instead of dying.
Reads are exempt: a gate you clear forty times is a gate you stop reading.

**`step5_persistence.py`** adds `scratch/state.json`, written after every
iteration. The real content is the distinction it forces: **state** is what is
true now, **history** is what happened this run and mostly should not survive,
**memory** is what survives on purpose and arrives in step 7. Resume is keyed
on the goal, and that one `if` is the whole safety property.

**`step6_compaction.py`** adds `compact_history()`. `search_docs` returns 2,000
words per call, so `--no-compact` makes the growth impossible to miss in the
`in=` column. Compaction keeps the goal, keeps the last two turns verbatim, and
replaces the rest with one model call. It prints the before and after token
count, so the saving is a number. It is lossy, by a model, trusted by the next
turn without review, and the interesting question is which run that kills.

**`step7_memory.py`** adds `scratch/memory.md`, read in on the way in and
appended to once on the way out. Day one derives which named person owns
Payments tickets. Day two, a fresh process with a different goal, finishes
with zero tool calls. The learning prompt is mostly a list of things NOT to
keep, which is the honest shape of a memory policy. This file is semantic
memory; a skill file the agent follows is procedural; a timestamped log of
runs is episodic. All three are text files.

**`step8_subagents.py`** adds `run_subagent()` and the budget layer.
`--single-context` shows one agent carrying thousands of words of raw research
into a turn that needed five lines of it. The default run gives the reading job
a child with a fresh history, a one-tool list and its own step budget, and the
child hands back a validated dict with `recommendation`, `important_facts` and
`sources`. It never raises: a failed child returns a structured failure and the
parent decides. The same file carries `MAX_STEPS`, `MAX_TOKENS`, `MAX_COST` in
rupees, and `no_progress()`, which is the cheap check, because repetition and
failure are properties of the history you already hold.

**`step9_sdk.py`** is the same system in the OpenAI Agents SDK, in about forty
lines, with the mapping table at the top of the file. Nothing new happens. The
loop did not disappear; you stopped writing it.

</details>

### The demo flags

Every failure in Part 2 has a switch, so you can fire it on cue rather than
hoping. Run the plain command first, then the flag, and compare.

| Command | What it makes visible |
|---|---|
| `python3 step5_persistence.py --kill-at 2` | Exits at iteration 2, as if you had hit Ctrl-C. Run it again with no flag and watch it resume. |
| `python3 step5_persistence.py --fresh` | Deletes `scratch/state.json` first, so you can replay the cold start. |
| `python3 step6_compaction.py --no-compact` | The same goal with compaction off. Read only the `in=` column. |
| `python3 step7_memory.py --reset` | Wipes `scratch/memory.md`, so day one is genuinely cold. |
| `python3 step8_subagents.py --single-context` | Both phases in one context, so you can see the research crowding the build. |
| `python3 step8_subagents.py --runaway` | A goal that needs a tool which always fails. `no_progress()` stops it, not the clock. |

Everything any tool writes goes into `scratch/`, and a path check refuses
anything that resolves outside it. That directory is the blast radius, and it
is deliberately small enough that you can point a live agent at it on a stage.

### One thing to check before you run steps 6 and 8

Those two files are about context growth, so they deliberately spend tokens.
`search_docs` returns 2,000 words per call and every turn re-sends every turn
before it, which is the entire point and also the entire cost.

A free Groq key allows 8,000 tokens per minute and 200,000 per day. Steps 6
and 8 will bump into both. If you are running the whole lab on a free key,
turn the prop down first:

```bash
export SEARCH_WORDS=600
```

The climb, the compaction and the sub-agent hand-back all still show clearly
at 600 words, and the day's allowance goes about three times further. Leave it
at 2,000 on a paid key, where the numbers are more dramatic. If you hit either
ceiling anyway, the run says so in one sentence instead of a stack trace:
`OUT OF TOKENS` for the daily quota, `THE WALL` for a single request that does
not fit.

### What Part 2 adds to the box

```
harness.py           the shared plumbing for steps 4 to 9. no lessons in it.
scratch/             the blast radius. every file tool is confined here.

step4_permissions.py the interlock
step5_persistence.py state, and what deliberately does not survive
step6_compaction.py  the trade you make when context runs out
step7_memory.py      what is still true tomorrow
step8_subagents.py   a second context, and the budget that bounds it
step9_sdk.py         the same system, in somebody else's words
```

`harness.py` holds the scratch guard, the five new tools, a token meter, and
the `plan` / `act` / `reflect` steps that every file from 4 to 8 reuses
unchanged. It is there so each step file is a readable delta and nothing else.
`SENSE` and `OBSERVE` are not in it: step 3 derived both and neither was
deleted from the idea, they are simply left out of Part 2 so a live log fits on
a screen.

Two numbers now print on every model call: the tokens that call cost, and the
running total in rupees. In step 2 the budget was iterations, because
iterations were the only thing we could count.


## If something goes wrong

| Symptom | Fix |
|---|---|
| `The api_key client option must be set` | `export GROQ_API_KEY=gsk_...` |
| `model does not exist or you do not have access` | That model was retired. Pick a live one from <https://console.groq.com/docs/models> and `export MODEL=...` |
| A run pauses for a few seconds | A rate limit on the free key. The client waits and retries by itself. |
| A step shows `None({})` or `none({})` | Expected in step 2. The model has worked the answer out and we have given it no way to say so, so it flails. That is the point of step 2. |
| `ModuleNotFoundError: groq` | `pip install groq` |
| `ModuleNotFoundError: step1_one_shot` | Run from the repo root, not from another directory. |
| `ModuleNotFoundError: agents` or an `openai` import error in step 9 | `pip install -U openai-agents`. It is the one library steps 1 to 8 refuse, and only step 9 needs it. The `-U` matters: the SDK needs a recent `openai` package. |
| A step 4 run prints `permission denied by user` and then finishes anyway | Working as intended. Denial is returned to the agent as a tool result, so it adapts. Answer `y` at the prompt to see the other branch. |
| `refused: ... is outside scratch/` | Also working as intended. Every file tool is confined to `scratch/`. Nothing in this repo can write anywhere else, including in a demo that goes wrong. |
| Step 5 resumes when you wanted a cold start, or says `ALREADY DONE` | `scratch/state.json` is left over from an earlier run of the same goal. `python3 step5_persistence.py --fresh` deletes it. |
| Step 7 answers day one instantly, or from a stale fact | `scratch/memory.md` already has a line in it from a previous run. `--reset` wipes the file. That is also the failure mode the file is about: nothing in it ever deletes a line, and nothing ever checks one. |
| A step 6 or step 8 run is slow | `search_docs` returns 2,000 words per call on purpose, and those words are re-sent every turn. That slowness IS the failure the file exists to show. |
| `OUT OF TOKENS`, or a 429 naming tokens per day | Your key's daily allowance is spent. Wait for the window Groq names, use another key, or `export SEARCH_WORDS=600` and re-run. |
| `THE WALL`, or a 413 naming tokens per minute | One request was larger than your key is allowed to send. On a free key that is 8,000 tokens. In step 6 with `--no-compact` this is not a fault, it is the demo. |
