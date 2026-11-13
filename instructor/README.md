# Instructor notes (do NOT give to students)

## What is where
| path | purpose |
|---|---|
| `student/secure_codegen_lab.ipynb` | the Colab notebook students run (self-contained) |
| `student/README.md` | the handout (tasks, grading, troubleshooting) |
| `lab/` | source of everything in the notebook. Rebuild the notebook after editing: `python lab/build_notebook.py` |
| `data/cases.jsonl` | the 21 benchmark cases (embedded in the notebook) |
| `instructor/ANSWER_KEY.md` | grading notes and expected answers for every task |
| `instructor/secure_codegen_lab_SOLUTION.ipynb` | same notebook as the student one, except Step 4 contains the reference strategies and the answer cells have sample answers |
| `instructor/solution/` | reference strategies `s1_role.py` ... `s4_two_stage.py` and their run (`solution_runs.jsonl`) |
| `instructor/tools/run_notebook_test.py` | runs a notebook end-to-end like Colab (to test it yourself) |
| `instructor/reference/` | reference run, scores, reliability audit |
| `data/seccodeplt/`, `lab/testrunner.py`, `lab/select_cases_v2.py` | OPTIONAL advanced set (see below), not used by the notebook |

## Setup choices (and why)
* **Model: Qwen3-1.7B.** Qwen3 has no 3B size. It fits a free Colab T4 in fp16 (~3.5 GB).
* **Benchmark: SecurityEval** (HF `s2e-lab/SecurityEval`, 121 prompts, Python, CWE-labelled).
* **Scorer: Bandit 1.9.4 only** (pinned, because the set of "detectable" cases depends on the Bandit version). The original paper used CodeQL + Bandit + human judgement; the repo ships **no** scoring script, only the Bandit command, CodeQL shell scripts with the author's hard-coded paths, and an empty CSV template for manual labelling.
* **Case selection:** a case is kept only if Bandit flags the dataset's own `Insecure_code` with the labelled CWE (`lab/select_cases.py`). 23 pass; 2 more are dropped because they were only flagged by informational checks (see next point) → **21 cases, 15 CWEs**.
* **Bandit noise filter (a deviation from a plain `bandit` run):** Bandit reports B404/B603/B607 etc. on any `subprocess` use, even in correct code, and the CWE tag is the same (CWE-78). Counting them marks safe code as vulnerable, so `lab/scorer.py` ignores B401–B415, B603, B607. Mention this when students ask why their number differs from a plain run.
* **Decoding:** greedy, `repetition_penalty=1.05`, `max_new_tokens=2048`, thinking mode off (Qwen3 `enable_thinking=False`), so "CoT" is purely prompt-based.
* The scorer never **executes** generated code (Bandit is static), so the notebook is safe to run.

## Grading
See `ANSWER_KEY.md`: Task 1 setup check = 4 pts, four prompt strategies = 4 x 24 pts, graded on process (implemented / 2+ versions logged / honest interpretation), **not** on beating `base`.

## Reference results (Qwen3-1.7B, 21 cases, RTX 4060, batch 8)
| method | valid% | func% | vuln% | SECURE% |
|---|---|---|---|---|
| base | 100 | 100 | 57.1 | **42.9** |
| sec_instruct | 95.2 | 95.2 | 42.9 | 52.4 |
| few_shot | 100 | 100 | 47.6 | 52.4 |
| cot | 100 | 100 | 23.8 | **76.2** |
| cot_fewshot | 100 | 100 | 52.4 | 47.6 |
| cwe_hint (oracle) | 100 | 100 | 33.3 | 66.7 |
| self_refine | 95.2 | 95.2 | 42.9 | 52.4 |

Per-CWE table: `instructor/reference/scores_table.txt`. One case = 4.8 points; treat gaps of ≤ 2 cases as noise.

Reliability audit (`audit_report.txt`): 0/147 parser problems, 0 Bandit crashes, 2/147 truncated (both `CWE-377_codeql_1`, under `sec_instruct` and `self_refine`; the model hit the 2048-token limit).

Things worth discussing in class / likely good student findings:
* `cot` beats even the oracle `cwe_hint`; `cot_fewshot` does not. Longer context is not automatically better for a 1.7B model.
* No method passes CWE-22 or CWE-319. Careful: the CWE-22 case is a **scorer artifact** (Bandit B310 fires on any `urlopen`, even after a correct fix), while CWE-319 is winnable with `ftplib.FTP_TLS`. See `ANSWER_KEY.md`. Only `cot` passes one of the two CWE-78 cases.
* `sec_instruct` and `self_refine` produce a few unparsable/truncated outputs, i.e. "more security text" has a functionality cost.
* `base` is not the worst everywhere: on CWE-605, `sec_instruct` and `self_refine` are *worse* than `base`.

## Known limits (also in the handout)
* Bandit has false negatives (rules cover only some CWEs) and false positives. "Secure" = "not flagged".
* 21 cases and one greedy sample: small effects are noise.
* Different GPU / `transformers` version can flip 1–2 cases. Do not grade on exact equality with the reference.

## Things we tried and why they are not in the notebook
* **SecCodePLT** (`Virtue-AI-HUB/SecCodePLT`): ships executable *capability* and *safety* tests, which is the better scorer in principle. With Qwen3.5-2B only 7–17% of samples passed functionality + safety, so prompt methods could not be separated. The code is in `lab/` for an optional harder extension (`lab/select_cases_v2.py`, `lab/testrunner.py`). **It executes model-generated code**, with only time/memory limits and no real sandbox; run it in a container or on Colab, never on a shared machine.
* **CyberNative/Code_Vulnerability_Security_DPO**: no executable tests, and only 77 of its 349 Python rows (after removing tasks whose text leaks the security requirement) had a "vulnerable flagged by Bandit / fixed answer clean" pair. Those clustered in a few CWEs (mainly 78 and 89), so a diverse set of 20-30 was not possible. Dropped.

## Rebuilding / changing the lab
```
cd lab
python select_cases.py            # re-select cases (needs bandit + internet); overwrites data/cases.jsonl
python build_notebook.py          # regenerate student/secure_codegen_lab.ipynb
python build_notebook.py --solution   # regenerate instructor/secure_codegen_lab_SOLUTION.ipynb (needs instructor/solution/s1..s4)
python generate.py --out ../results/run.jsonl && python evaluate.py ../results/run.jsonl
```
If you change a prompt in `prompts.py` or the case list, regenerate the reference results and update the table above and `student/README.md`.
