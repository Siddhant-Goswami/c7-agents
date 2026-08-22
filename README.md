# Module 3 · Lecture 2 — Deriving the Agent Loop

**100xEngineers · Cohort 7 · Live coding lab · ~90 minutes**

---

## The brief

Last session ended with a definition. Tonight we do not trust it — we try to
derive it.

We start with a program you already wrote in Module 2:

```python
result = get_weather("Bangalore")
answer = llm(user_query, result)
```

We end with the minimal agent loop. Between those two points we introduce
almost nothing new. Sensing came out of context engineering. Planning came out
of the LLM lecture. Acting came out of tool calling. Observation came out of
the augmentation step. Every piece is already in your hands. What changes is
the **order they run in**, and the fact that they now **repeat**.

So the whole session answers exactly one question:

> **What is the minimum we must add to this program so that the *software*,
> rather than the *human*, decides what happens next?**

### The one rule for tonight

**You predict every new abstraction before I type it.**

Every file ends in a `PREDICT` block. Those are not homework — they are the
next line of code, and you write them, not me. If you scroll ahead to the
answer you will have learned five boxes instead of six failure modes, and
five boxes are worth nothing.

By the last file you will discover you have reconstructed **SPAOR** yourselves,
and you will be able to say, for each letter, which specific failure comes
back if you delete it.

### What you leave with

- A working agent in ~19 lines of Python, no framework, no library, no vendor.
- The ability to look at any agent product — Claude Code, Codex, an Agent SDK —
  and name which box each part of it is, and which decisions it hid from you.
- A stopping condition you can defend from a budget.

---

## Before the lecture (5 minutes, do it today)

```bash
git clone <this repo> && cd c7-agents

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # then paste your Groq key into .env
python setup_check.py         # must print OK three times
```

Your key is the same one from the Module 2 tool-calling lecture.
A free one takes 30 seconds: <https://console.groq.com/keys>

If `setup_check.py` fails, fix it **today**. Not at minute four of the session.

---

## Running the lab

Everything runs from the project root, one file at a time, in order:

```bash
python steps/step_00_one_llm_call.py
python steps/step_01_llm_plus_tool.py
...
python steps/step_12_loop_engineering.py
```

In the live session we grow **one** file. These thirteen files are the
checkpoints along the way — each one is complete and runnable on its own, so
if you fall behind you can jump to the next one and catch up instantly. Step
N+1 always contains the answer to step N's `PREDICT` block.

---

## The seven discoveries

| # | File | You answer | You discover |
|---|------|-----------|--------------|
| — | `step_00`, `step_01` | *Is this an agent?* | It is not. The LLM participates in the workflow; it does not control it. |
| — | `step_02` | *Who decides what happens next?* | A human does — the user when it works, the builder when it breaks. Neither scales. |
| 1 | `step_03` | *What prevents autonomy from becoming an infinite bill?* | **The stopping condition** |
| 2 | `step_04` | *What Python primitive allows another attempt?* | **The loop** |
| 3 | `step_05` | *What must iteration 2 know about iteration 1?* | **State** |
| 4 | `step_06` | *What does the model need to know before deciding?* | **Sense** |
| 5 | `step_07` | *Should the model act immediately?* | **Plan** |
| — | `step_08` | *Why not let the LLM run arbitrary Python?* | The boundary between probabilistic judgement and deterministic execution |
| 6 | `step_09` | *Is a tool result the same as knowing what happened?* | **Observe** |
| 7 | `step_10` | *Who decides whether we stop or try something else?* | **Reflect** — and the loop closes |
| — | `step_11` | — | It has a name: **SPAOR** |
| — | `step_12` | *Would ten teams with this same agent perform equally?* | **Loop engineering**, and what an SDK actually hides |

---

## What's in the box

```
agent_lab/
  llm.py        the probabilistic half — two functions, given to you
  tools.py      the deterministic half — two weather tools, given to you
  display.py    printing helpers, not part of the idea

steps/
  lab.py        import plumbing, not part of the idea
  step_00 … step_12    the derivation

setup_check.py  run this before the lecture
```

**`llm.py` and `tools.py` are the only things handed to you.** Everything else
in this repository is built tonight, live, out of those two files plus a
dictionary and a Python list.

The weather data is real, from [Open-Meteo](https://open-meteo.com) — free,
no key, no signup. Responses cache to `.cache/`, so re-running a step during
the lecture is instant and does not depend on the venue wifi.

---

## Notes

- The year literals in the goals (`2021…2025`) are the last five completed
  Augusts as of this cohort. Bump them next year.
- `agent_lab/tools.py` contains one deliberate, real bug fix worth reading:
  the geocoder resolves `"Bangalore"` to a neighbourhood in **Karachi**. It
  returns HTTP 200 and perfectly well-formed rainfall data for the wrong
  country. Keep that in your pocket for step_09 — it is the cleanest possible
  argument that a *result* is not an *observation*.
