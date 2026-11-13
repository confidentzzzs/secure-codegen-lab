# Answer key and grading notes (instructor only)

Numbers: Qwen3-1.7B, SecurityEval subset (21 cases, 15 CWEs), Bandit 1.9.4, greedy decoding. **One case = 4.8 points.**
Different GPUs / library versions can move 1-2 cases, so never grade on exact numbers.

## Structure (100 pts)
The student notebook has 5 blank answer cells titled "✏️ YOUR ANSWER". `instructor/secure_codegen_lab_SOLUTION.ipynb` has the same cells filled with sample answers and the reference strategy code.

| Part | Points | Where |
|---|---|---|
| Task 1: setup check | 4 | answer cell after the score table |
| Strategy 1: role / system prompt | 24 | Step 4a cell + answer cell |
| Strategy 2: few-shot with own examples | 24 | Step 4b |
| Strategy 3: structured reasoning / checklist | 24 | Step 4c |
| Strategy 4: two-stage | 24 | Step 4d |

## Task 1: setup check (4 pts)
Full marks if the score table is pasted and looks like a real run (7 methods, 21 cases each). Do **not** grade on the numbers. Reference run:

| method | valid% | func% | vuln% | SECURE% |
|---|---|---|---|---|
| base | 100 | 100 | 57.1 | 42.9 |
| sec_instruct | 95.2 | 95.2 | 42.9 | 52.4 |
| few_shot | 100 | 100 | 47.6 | 52.4 |
| cot | 100 | 100 | 23.8 | 76.2 |
| cot_fewshot | 100 | 100 | 52.4 | 47.6 |
| cwe_hint (oracle) | 100 | 100 | 33.3 | 66.7 |
| self_refine | 95.2 | 95.2 | 42.9 | 52.4 |

Per-CWE table: `reference/scores_table.txt`.

## The four strategies: rubric (24 pts each)
| pts | criterion | what to check |
|---|---|---|
| 4 | implements the strategy as defined and runs | the file is the right kind of strategy (below); `generate.py` accepted it (it refuses answer-key use automatically) |
| 10 | at least 2 versions tried and logged | a table `version / what changed / SECURE%`; the versions must actually differ; scores must be plausible (re-run the cell if in doubt) |
| 10 | honest interpretation | result vs `base` in **number of cases**; says whether it is more than noise (1 case = 4.8 pts); a reason that refers to the generated code (the Step 3b helper) |

**Do not grade on beating `base`.** A strategy that fails but is explained well gets full marks. A +1 or +2 case gain claimed as a success, with no mention of noise, loses interpretation points.

"As defined":
* **S1 role:** only the system prompt differs from `base`; the user message is unchanged.
* **S2 few-shot:** at least 2 own demonstrations about functions that are not benchmark tasks (the guard refuses pasted benchmark tasks); not a copy of the built-in `FEWSHOT`.
* **S3 structured:** a scaffold (checklist / reasoning steps) added before the code is written; the same for every case.
* **S4 two-stage:** two model calls; stage 2 uses stage 1's answer; it must differ from the built-in `self_refine` (a generic "review and fix your code" is not enough).

## Reference solutions and what to expect
Files: `solution/s1_role.py` ... `s4_two_stage.py`; run outputs in `solution/solution_runs.jsonl`. Baseline `base` = 42.9%.

| strategy | reference design | SECURE% | vs base |
|---|---|---|---|
| S1 | detailed "senior security engineer at a bank" role in the system prompt | 52.4 | +2 cases |
| S2 | 3 own demos on XSS, open redirect, timing attack (not in the benchmark) | 47.6 | +1 case |
| S3 | security checklist + "name at most 3 items that apply, THEN code" | **61.9** | +4 cases |
| S4 | stage 1: list at most 3 attack scenarios (no code); stage 2: code that defends against them | 47.6 | +1 case |

What to expect from students and what is true in our run (so you can recognize a real insight):
* **Only S3 gave a clear gain.** S1, S2 and S4 are within noise of `base`. Do not expect most students to beat `base` on every strategy.
* **Long prompts hurt a 1.7B model.** The same checklist *without* the "name which items apply" step scored **38.1%**, below `base`, with only 76% of outputs parsing. A student who finds this (shorter or structured scaffold beats a long one) shows real understanding.
* **A one-line instruction already gives most of the S1 gain:** the built-in `sec_instruct` also scores 52.4%.
* **Demos help most on the same vulnerability type.** The built-in `few_shot` (demos on command injection, SQL, hashing, which overlap the benchmark CWEs) scored 52.4%, higher than our out-of-benchmark demos (47.6%).
* **Two stages double the time** and a self-written plan is not necessarily followed in the code.
* Insights about the scorer are also worth credit: passing Bandit is not the same as being secure, and the CWE-22 case (`readJSON`) is a **scorer artifact** (Bandit B310 flags every `urlopen`, even after a correct fix, so that case can only pass by avoiding `urlopen`). CWE-319 (FTP) is winnable with `ftplib.FTP_TLS`.
* Our S3 was tuned on the same 21 cases, so it may be partly overfit; the solution is an example, not a ceiling.

## Frequent problems
* A student's prompt that mentions a CWE number in a generic list (for example "CWE-78, CWE-89") is **fine**: the guard only refuses prompts that differ between cases.
* If a student's strategy is identical in effect to `base` (the template unchanged) the score will equal `base` (42.9%): no credit for implementation.
* Truncated outputs (2048-token limit) count as failures; `audit.py` lists them. Long few-shot or checklist prompts make this more likely.
