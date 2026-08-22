# Building the Agent Loop From First Principles

**100xEngineers · Module 3 · Hands-on lab**

---

## What this is

You already know how to call an LLM, call an API, engineer context, and
augment a prompt with retrieved data. This lab introduces almost nothing new.

It starts with a program you already wrote in Module 2:

```python
result = get_weather("Bangalore")
answer = llm(user_query, result)
```

and ends with a working agent, in about nineteen lines of Python. No
framework, no library, no vendor. Between those two points, every piece is
something you already have — what changes is the **order** the pieces run in,
and the fact that they now **repeat**.

The whole lab answers one question:

> **What is the minimum we must add to this program so that the *software*,
> rather than the *human*, decides what happens next?**

### The one rule

**Predict every new abstraction before you read it.**

Every file ends in a `PREDICT` block. Those are not homework and they are not
optional — they *are* the lab. Each one asks you the question that makes the
next abstraction necessary, and the next file contains the answer.

If you skim straight through, you will end up having memorised a diagram. If
you answer the questions first, you will end up able to say — for every single
piece — exactly which failure comes back if you delete it. That second thing
is the point.

### What you leave with

- A working agent you wrote yourself, with no framework involved.
- The ability to look at any agent product — Claude Code, Codex, an Agent
  SDK — and name what each part of it is doing and which decisions it hid.
- A stopping condition you can defend from a budget.

---

## Setup (5 minutes)

You need Python 3.9 or newer and a terminal. Check with `python3 --version`.

**1 · Get the code**

```bash
git clone https://github.com/Siddhant-Goswami/c7-agents.git
cd c7-agents
```

**2 · Create a virtual environment**

macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

You'll know it worked when your prompt starts with `(.venv)`. You need to run
the activate line again each time you open a new terminal.

**3 · Install the three dependencies**

```bash
pip install -r requirements.txt
```

**4 · Add your API key**

```bash
cp .env.example .env
```

Then open `.env` in any editor and replace `gsk_replace_me` with your Groq
key — the same one from the Module 2 tool-calling lecture. A free key takes
about 30 seconds: <https://console.groq.com/keys>

`.env` is gitignored, so your key never leaves your machine.

**5 · Check it all works**

```bash
python setup_check.py
```

You want three `OK`s. If you get them, you're ready. Do this step *before*
the session, not during it.

---

## How to work through the lab

Thirteen files, in order, from `step_00` to `step_12`.

For each one:

1. **Open the file and read the docstring at the top.** It sets up a problem
   and asks you a question.
2. **Answer the question.** Write it down. Do not skip this.
3. **Run the file** from the project root:
   ```bash
   python steps/step_00_one_llm_call.py
   ```
4. **Read the `PREDICT` block at the bottom.** It asks what has to come next.
   Answer that too, before you open the next file.
5. **Open the next file.** It contains the answer, and the next problem.

Every file is complete and runnable on its own, so if you get stuck or fall
behind you can jump straight to the next one and carry on without breaking
anything.

Run the files from the **project root** (the folder with `README.md` in it),
not from inside `steps/`.

---

## The path

| # | File | The question you answer |
|---|------|------------------------|
| 00 | `step_00_one_llm_call.py` | What is this program missing? |
| 01 | `step_01_llm_plus_tool.py` | Is this an agent? |
| 02 | `step_02_the_query_that_breaks_it.py` | Who decides what happens next? |
| 03 | `step_03_stop.py` | What prevents autonomy from becoming an infinite bill? |
| 04 | `step_04_loop.py` | What Python primitive allows another attempt? |
| 05 | `step_05_state.py` | What must iteration 2 know about iteration 1? |
| 06 | `step_06_sense.py` | What does the model need to know before deciding? |
| 07 | `step_07_plan.py` | Should the model act immediately? |
| 08 | `step_08_act.py` | Why not just let the LLM run arbitrary Python? |
| 09 | `step_09_observe.py` | Is a tool result the same as knowing what happened? |
| 10 | `step_10_reflect.py` | Who decides whether we stop or try something else? |
| 11 | `step_11_the_minimal_agent.py` | — the thing you built gets its name |
| 12 | `step_12_loop_engineering.py` | Would ten teams with this agent perform equally? |

<details>
<summary><b>Spoilers</b> — what each step actually adds. Open only if you are stuck.</summary>

<br>

| File | What appears, and why |
|------|----------------------|
| `step_03` | **The stopping condition.** Without it, a loop that cannot solve the problem runs until your budget is gone. |
| `step_04` | **The loop.** Without it, the program gets exactly one attempt at the goal. |
| `step_05` | **State.** Without it, iteration 2 is just iteration 1 happening again. |
| `step_06` | **Sense.** Without it, the model decides what to do without knowing where it is. |
| `step_07` | **Plan.** Without it, sequence is left to chance — and sequence is part of correctness. |
| `step_08` | **Act**, and the boundary between the model's judgement and your runtime's control. |
| `step_09` | **Observe.** Without it, a 200 response gets mistaken for a correct answer. |
| `step_10` | **Reflect.** Without it, nothing can decide whether the loop should continue. This is the one that turns the program into an agent. |
| `step_11` | All six together, named. |

</details>

---

## What's in the box

```
setup_check.py     run this first

agent_lab/
  llm.py           two functions that call an LLM — given to you
  tools.py         two weather tools — given to you
  display.py       printing helpers, not part of the idea

steps/
  lab.py           import plumbing, not part of the idea
  step_00 … step_12   the lab itself
```

**`llm.py` and `tools.py` are the only things handed to you.** Everything else
is built during the lab out of those two files, plus a dictionary and a list.

The weather data is real, from [Open-Meteo](https://open-meteo.com) — free, no
key, no signup. Responses are cached to `.cache/`, so re-running a step is
instant and doesn't depend on your wifi. Delete that folder any time to fetch
fresh data.

---

## If something goes wrong

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'lab'` | You ran the file from inside `steps/`. Go back to the project root and run `python steps/step_00_one_llm_call.py`. |
| `ModuleNotFoundError: No module named 'groq'` | The virtual environment isn't active, or dependencies aren't installed. Re-run the activate line, then `pip install -r requirements.txt`. |
| `No GROQ_API_KEY found` | You haven't created `.env` yet, or the key in it is still `gsk_replace_me`. See setup step 4. |
| `model ... does not exist` or a 404 from Groq | The default model was retired. Open `.env`, change `GROQ_MODEL` to another one from <https://console.groq.com/docs/models>, and every file picks it up. |
| A step is slow the first time | It's fetching real weather data. It caches, so the second run is instant. |
| The agent gives a wrong or partial answer | Good — that's material. Which step failed: sense, plan, observe, or reflect? That question is what `step_12` is about. |
| The run hits `MAX_STEPS` with no answer | Not a bug. That's the boundary from `step_03` doing its job. |
| Rate-limited by Groq | Free tier limits requests per minute. Wait a minute and re-run; cached weather calls won't re-fetch. |

Still stuck? Bring the exact error text to the cohort channel — the traceback
matters more than the description.
