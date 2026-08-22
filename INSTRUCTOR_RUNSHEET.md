# Instructor runsheet — Lecture 2, Deriving the Agent Loop

**~90 minutes. One continuous program. Students type along.**

The core rule, restated for you: **do not type an abstraction before the room
has predicted it.** The room's wrong answers are the lecture. If you find
yourself explaining a box, you have already lost that box — back up and ask
the question that makes it necessary.

Do not show SPAOR until step_11. Not on a slide, not in passing, not on the
whiteboard. If someone says it early, take it and park it: *"hold that word,
we'll see if we need it."*

---

## Before you go live

```bash
source .venv/bin/activate
python setup_check.py                  # confirms key + model + API
python steps/step_11_the_minimal_agent.py   # warms .cache/, ~60-90s
```

Running step_11 once in advance populates the disk cache, so every weather
call during the live session is instant. Do this. It removes the single
biggest source of dead air.

Have a second terminal open on `steps/step_11_the_minimal_agent.py` as your
safety net if the live buffer goes wrong.

---

## Timing

| Time | Step | Beat |
|------|------|------|
| 0–5 | — | Frame. One question, no slides. |
| 5–12 | `step_00`, `step_01` | Is this an agent? |
| 12–20 | `step_02` | The query that breaks it. Who decides what happens next? |
| 20–26 | `step_03` | **Discovery 1 — STOP** |
| 26–33 | `step_04` | **Discovery 2 — LOOP** |
| 33–42 | `step_05` | **Discovery 3 — STATE** |
| 42–50 | `step_06` | **Discovery 4 — SENSE** |
| 50–58 | `step_07` | **Discovery 5 — PLAN** |
| 58–64 | `step_08` | ACT, and the boundary you designed |
| 64–71 | `step_09` | **Discovery 6 — OBSERVE** |
| 71–80 | `step_10` | **Discovery 7 — REFLECT.** The loop closes. |
| 80–86 | `step_11` | Run it. Only now: name it SPAOR. |
| 86–90 | `step_12` | Loop engineering, SDK reveal, closing challenge. |

If you are running long, the compressible beats are step_04 (2 min) and
step_08 (3 min). **Never compress step_09→step_10.** That transition is the
entire lecture; everything before it is setup for it.

---

## 0–5 · Frame

Say roughly this, then stop talking:

> Last session ended with a definition. Today I don't want you to trust it.
> I want to see whether we can derive it. You already know how to call an LLM,
> call an API, engineer context, and augment. So today I introduce almost
> nothing. And I'm not going to give you the code — you're going to tell me
> what line comes next.

Do not preview the agenda. The absence of a roadmap is the pedagogy.

---

## 5–12 · step_00 → step_01 · Is this an agent?

Run `step_00`. The model confidently invents the weather. Ask what's missing.
They'll say live data. Run `step_01`.

Then walk the four questions slowly. Make them answer each one out loud:

- Who decided `get_weather()` should be called? → *we did*
- Who decided `"Bangalore"` was the argument? → *we did*
- Who decided to send the result back to the model? → *we did*
- Who decides what happens after `print(answer)`? → *the user*

Draw it: `Human → LLM → Tool → LLM → Human`

**Land this sentence and let it sit:** the LLM *participates* in this
workflow. It does not *control* it.

Then ask directly: is this an agent? You want a clear **no**, and you want
someone to try to name what's missing. Take every answer. Do not correct any
of them yet.

> ⚠️ Someone will say "memory" or "a loop" here. Both are right, and it is far
> too early. Write them on the board, unlabelled, and say *"remember you said
> that."* You will point back at the board twice tonight.

---

## 12–20 · step_02 · The query that breaks it

Read the wedding query out loud before running anything. Then ask, in order:

1. How many tool calls does this need?
2. Do we know, before starting, exactly which ones?
3. What happens if one fails?
4. What if what comes back changes what we need next?

Run it. **ATTEMPT A** answers about one year — and had no way to know it was
under-informed. **ATTEMPT B** either fits or throws a context-window error.
Both outcomes work for you:

- If it errors: *"same failure as the tool-calling practical. It breaks at the
  boundary rather than degrading quietly."*
- If it fits: *"fine — now look at what we just did."*

Either way, point at the human fingerprints in ATTEMPT B: `range(2016, 2026)`,
the comprehension, the single final call. **We** chose all of it, in advance,
in the source.

Close the beat on Lecture 1's claim: output correct → the user decides what's
next. Output wrong → the builder decides. Either way a human decides, and
humans do not scale like servers do.

Then put the session's only question on screen and leave it there.

---

## 20–26 · Discovery 1 · STOP (`step_03`)

Do **not** go to the loop yet. This ordering is deliberate and it is the part
most instructors get backwards.

Paint the picture: weather call, think, weather call, think, forever.
*"What actually happens?"* — you want cost, tokens, latency, a runaway
process. Then: *"So before we create autonomy, what goes around it?"*

Type one line. `MAX_STEPS = 5`.

Then make someone **defend the number from a budget**, not from taste. If the
room says "5 feels right", push back until you get something shaped like
*"one iteration is ~4 calls, ~$0.002, I'll spend a cent, so 5."*

Land: autonomy without a boundary is not engineering, it's an uncontrolled
process. Decide when to pull the plug **before** you run it, not after the bill.

---

## 26–33 · Discovery 2 · LOOP (`step_04`)

*"Our program gets one chance. What is the minimum Python construct that
gives it another?"* Wait for **loop**. Do not accept "agent loop".

Then: `while` or `for`? Let them argue briefly. Land on `for` because
`range(MAX_STEPS)` **is** the stopping condition — the budget lives in the
loop's own signature.

Run it. Three identical iterations. Then the question that opens Discovery 3:

> *"What is different between iteration 1 and iteration 3? So is that really
> iteration 3 — or is it iteration 1, happening again?"*

Land: a loop that can't tell its turns apart is repetition, not iteration.
We bought three chances and spent them all on the same chance.

---

## 33–42 · Discovery 3 · STATE (`step_05`)

Ask what iteration 2 would need to know about iteration 1. Write every answer
on the board: tool called, result, failures, previous reasoning, the goal.

Then: *"what's the smallest Python object that holds that?"*

Type `history = []`. Then ask them what goes in it after every iteration, and
let them dictate `history.append(...)`.

Run it. Now the honest bit — and do not skip it:

> *"Did the answer change? No. Why not? The past is right there."*

**The system has a memory that nothing reads.** That gap is what makes SENSE
necessary. Point back at the board: this is the memory lecture, and tonight it
is an embarrassing Python list. That's fine. Architecture first.

---

## 42–50 · Discovery 4 · SENSE (`step_06`)

*"Before the model decides what to do, what does it need to know?"*

Collect everything: goal, user request, history, environment, previous
results, available tools, permissions. Circle all of it and ask what you'd
call the act of constructing that picture. You'll get context, state,
perception. Take "sensing" when it arrives, or supply it via the Roomba: the
best cleaning algorithm ever written, with no sensor for where it is, cleans
nothing. Perception comes before planning.

Then the deflation, which matters: *"Is `sense()` magic? What could it
actually be?"* → **it's an LLM call.**

Run it. The three STATE blocks differ — first time iteration 2 is conditioned
on iteration 1. Then note that the model probably *told us* we fetched the
same year three times, and we ignored it.

---

## 50–58 · Discovery 5 · PLAN (`step_07`)

*"Now the model knows where it is. Should it call a tool immediately?"*

Make the task's size visible: ten years, ten calls, extract per weekend,
compare across years, handle a missing year, then conclude. *"What goes wrong
if it executes before deciding the sequence?"* → wrong ordering, wasted calls,
premature conclusion, nothing to verify against.

Land both reasons:
1. **Sequence is now part of correctness.** Predict before you fetch and the
   prediction is guaranteed wrong. The plan is where sequence lives.
2. **A plan is the cheapest artifact in the loop to check.** A plan costs one
   call; an action touches the world.

Show the JSON contract. Explain the switch from `llm` to `llm_json` in one
sentence: `if reflection["done"]` needs a dict, not a paragraph.

Run it, then point at the hardcoded `get_august_rainfall(...)` line and say
plainly: *"the model just told us what to call. We ignored it."*

---

## 58–64 · step_08 · ACT and the boundary

*"Why don't I just let the LLM write and run arbitrary Python?"* → security,
permissions, hallucinated tools, arbitrary side effects.

So the Python type is a **dict**. Type `TOOLS = {...}` and the dispatch line.

Put these two lines next to each other and slow down:

```
the_plan = plan(...)                       ← probabilistic judgement
TOOLS[action["tool"]](**action["args"])    ← deterministic execution
```

> **Who has more power here — the model or the developer?**

Let that run. Land: the model proposes, the runtime decides what actions exist
at all. The model has agency *inside a boundary we designed*. Flag forward —
this becomes central when we get to graph engineering: the developer designs
the possible world, the model decides how to move inside it.

Run it. Note aloud: **we did not write a single year number.** One decision
delegated.

---

## 64–71 · Discovery 6 · OBSERVE (`step_09`)

*"The API returned something. Does that mean the action succeeded?"*

Most rooms say yes. Then hit them with the four cases, one at a time:

- `{"status": 200, "data": []}` — succeeded?
- a 500
- rainfall data, but for Delhi
- real, useful data that is nowhere near enough for the goal

**Your best asset here is real:** `"Bangalore"` geocodes to a neighbourhood in
Karachi. HTTP 200, well-formed rainfall, wrong country. See `agent_lab/tools.py`.
Use it — it is far more convincing than a hypothetical.

Land the distinction and write it on the board:

> A **result** is what the environment returned.
> An **observation** is what that result **means for the task**.

Connect it back: in RAG, augmentation turned retrieved information into an
answer for the *user*. Here we turn tool output into an account for the
*model itself*. Not "what did the API say?" but "given my goal, what did I
just learn?"

---

## 71–80 · Discovery 7 · REFLECT (`step_10`) — the critical moment

Put the four-line loop on screen and **stop coding**.

> *"Are we done? Is this an agent?"*

Some will say yes. Do not help them quickly. Then:

- Who decides whether this result is enough?
- What if we only collected 2017?
- What if the tool failed?
- What if we already have all ten years and know the answer — what in this
  code stops it running twice more and spending your budget?
- What decides whether another iteration is necessary?

You want: evaluator, verifier, check the goal, the model. Take the evaluator
answer and use it to force the thing left unstated all evening: **you cannot
evaluate without a goal.** Then make the finer point — an evaluator gives you
a verdict, not a next move. Something still has to decide what more is needed.

Then ask the question this whole module has been asking:

> ### WHO DECIDES WHAT HAPPENS NEXT?

When someone says **"the model"** — do not agree, and do not type. Say
*"then write the line"* and let a student dictate it. Give it the contract.

Then the sentence the lecture exists for:

> *"Until this line, the model participated in the workflow. At this line, the
> model can decide whether the workflow continues. This is where 'what happens
> next?' leaves the human."*

Run it. Do not narrate over it. After each iteration ask:

- What changed? → **the state**
- What caused that? → **the consequences of the previous action**
- What changed the behaviour? → **the model saw the changed state**

Then draw the loop with the `done?` branch.

---

## 80–86 · step_11 · Name it

Only now, on the board:

# SPAOR

Walk it backwards — each box, and the problem that forced it:

| We needed | Box that appeared |
|---|---|
| the relevant state | **Sense** |
| sequence | **Plan** |
| to touch the world | **Act** |
| to understand the consequence | **Observe** |
| someone to answer "what happens next?" | **Reflect** |
| a boundary | **the stopping condition** |

Say it explicitly: *"this isn't an arbitrary framework — each abstraction
exists because removing it creates a specific failure mode, and you can name
the failure for every one of them."*

Show `step_11`'s loop. Nineteen lines. Not LangChain, not an Agent SDK, not
Claude Code, not Codex. **This.** Everything from here is improving one box,
constraining one, connecting several, or hiding them behind an abstraction.

---

## 86–90 · step_12 · Loop engineering

Run `python steps/step_12_loop_engineering.py` and work down it.

1. **Closing challenge** — labels off. Make them name every line.
2. **Ten teams, same agent, equal performance?** → no. Collect why, write the
   answers around the loop. That list *is* loop engineering, and it is the
   rest of the module. *"The loop isn't the hard part any more."*
3. **SDK reveal.** What disappeared? → history, the loop, tool dispatch,
   structured outputs, iteration handling, stopping logic, context management.
   *"Did the loop disappear? No. We stopped writing it. That's an
   abstraction."* Then: when is an abstraction useful, and when is it
   dangerous? → **when we no longer understand the assumptions it hides.**
4. **Codex / Claude Code.** Same shape, much better engineering. This is why
   we learn the primitive before the product.
5. **Close on Lecture 1's question.** *"What did we give the LLM that turned
   it into an agent?"* Not another model, tool, or API — a mechanism for
   experiencing the consequence of one decision and using it to make the next.
   Agency is the abstraction; the loop is the implementation.

Assign the three experiments and the four homework items in `step_12`. The
capstone tool-swap (item 2) is the one that matters: *"if the loop doesn't
survive the swap, that tells you something about the loop."*

---

## Traps and recoveries

| Situation | What to do |
|---|---|
| Someone says "SPAOR" or "ReAct" in the first 20 min | *"Hold that word. Let's see if we need it."* Park it on the board. Redeem it at step_11. |
| Room answers "yes, it's an agent" at step_01 | Don't argue. Ask the four who-decided questions instead and let the answers do it. |
| Nobody reaches "loop" at step_04 | Narrow it: *"you have one attempt and you need a second. What Python keyword?"* |
| Nobody reaches "evaluator" at step_09→10 | Ask *"what if we already have the answer — what stops it running again?"* The budget angle gets there fastest. |
| A live run produces a wrong or partial answer | **Use it.** *"Which box failed? Sense, plan, observe, or reflect?"* That is loop engineering happening live. |
| A run hits `MAX_STEPS` with no answer | *"Not a bug. That's the boundary you designed in step_03 doing its job."* |
| Model returns malformed JSON | `llm_json` already recovers from fences and prose. If it still fails, say so plainly — schema enforcement is a step_12 loop-engineering knob. |
| Running long | Compress step_04 and step_08. Never compress step_09→step_10. |
| API is slow or rate-limited | Weather is cached; only LLM calls hit the network. Fall back to your pre-run terminal and walk the output. |

---

## Maintenance

- Year literals (`2021…2025`) are the last five completed Augusts. Bump yearly.
- `GROQ_MODEL` in `.env` — if the default model is retired, one env var fixes
  every file.
- `rm -rf .cache/` to force fresh weather data.
