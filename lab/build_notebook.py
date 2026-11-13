"""Build the self-contained Colab notebooks from the sources in lab/ and data/cases.jsonl.
   python build_notebook.py              -> student/secure_codegen_lab.ipynb            (templates, empty answer blocks)
   python build_notebook.py --solution   -> instructor/secure_codegen_lab_SOLUTION.ipynb (reference strategies + sample answers)
"""
import json, os, sys
SOLUTION = "--solution" in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
def md(t): return {"cell_type": "markdown", "metadata": {}, "source": t.strip().splitlines(True)}
def code(t): return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": t.strip("\n").splitlines(True)}
def wf(path, text): return code(f"%%writefile {path}\n" + text.rstrip("\n"))
def read(p): return open(os.path.join(HERE, p)).read()
def tmpl(name): return read(os.path.join("templates", name + ".py"))
def sol(name): return open(os.path.join(ROOT, "instructor", "solution", name + ".py")).read()

def answer(title, points, hint, sample):
    """A markdown cell students fill in. In the solution notebook the sample answer replaces the blank."""
    body = sample if SOLUTION else "_(double-click this cell, delete this line and write your answer here)_"
    label = "SAMPLE ANSWER (instructor)" if SOLUTION else "YOUR ANSWER"
    return md(f"### ✏️ {label}: {title} ({points} pts)\n> {hint}\n\n{body}")

STRAT_HINT = ("(1) Your idea in 2-3 sentences. (2) A log of **at least 2 versions** you tried: `| version | what you changed | SECURE% |`. "
              "(3) Final result vs `base` in number of cases (1 case = 4.8 points): is that more than noise? "
              "(4) Why do you think it worked or not? (look at one case with the Step 3b helper). "
              "**Grading (24): 4 = implements the strategy as defined and runs; 10 = 2+ versions logged with scores; 10 = honest interpretation. You are NOT graded on beating `base`.**")

# ---------------- sample answers (instructor notebook only). Every number comes from the reference run.
S1 = """| table row | SECURE% |
|---|---|
| base | 42.9 |
| built-in `sec_instruct` (one-line "write secure code") | 52.4 |
| **my S1 (detailed "senior security engineer at a bank" role, 5 sentences)** | **52.4** |

Idea: only the system prompt changes (a persona that treats every argument as attacker-controlled and lists forbidden calls).
Result: +2 cases vs `base`, but exactly the same as the much shorter built-in `sec_instruct`. +2 cases is close to noise (1 case = 4.8 pts), so a long persona adds little beyond a one-line "be secure". *(A full answer lists the earlier versions you tried; this reference shows only the final one.)*"""
S2 = """| table row | SECURE% |
|---|---|
| base | 42.9 |
| built-in `few_shot` (demos on command injection, SQL, hashing: overlap the benchmark CWEs) | 52.4 |
| **my S2 (3 own demos: XSS `html.escape`, open-redirect check, `hmac.compare_digest`)** | **47.6** |

Idea: demos on vulnerability types that are *not* in the benchmark, to see whether secure habits transfer.
Result: +1 case vs `base` (noise level); lower than the built-in few-shot whose demos overlap the benchmark CWEs. Suggests demos help mostly when they show the *same* vulnerability type; this transfers poorly for a 1.7B model.
*(A full answer lists the earlier versions you tried.)*"""
S3 = """| table row | SECURE% | valid% |
|---|---|---|
| base | 42.9 | 100 |
| checklist only, no "which items apply" step | 38.1 | 76.2 |
| **my S3 (checklist + "name at most 3 items that apply, THEN code")** | **61.9** | 100 |

Idea: a short security checklist, then a forced one-line triage before the code.
Result: **+4 cases** vs `base`. The same checklist *without* the triage step was **worse than `base`** (valid only 76%): a long prompt made the 1.7B model write more broken code. So the short "which items apply" step is what made the checklist usable. 2 of the 21 outputs still hit the token limit (one case).
Caveat: tuned on the same 21 cases."""
S4 = """| table row | SECURE% |
|---|---|
| base | 42.9 |
| built-in `self_refine` (draft, then "review and fix") | 52.4 |
| **my S4 (stage 1: list <= 3 attack scenarios, no code; stage 2: write code that defends against them)** | **47.6** |

Idea: separate *thinking about attacks* from *writing code*, with the model's own list passed to stage 2.
Result: +1 case vs `base` (noise level), about 2x the generation time, and lower than the built-in `self_refine`. A plan the model wrote itself is not necessarily followed in the code."""
S_TASK1 = """| method | valid% | func% | vuln% | SECURE% |
|---|---|---|---|---|
| base | 100 | 100 | 57.1 | 42.9 |
| sec_instruct | 95.2 | 95.2 | 42.9 | 52.4 |
| few_shot | 100 | 100 | 47.6 | 52.4 |
| cot | 100 | 100 | 23.8 | 76.2 |
| cot_fewshot | 100 | 100 | 52.4 | 47.6 |
| cwe_hint | 100 | 100 | 33.3 | 66.7 |
| self_refine | 95.2 | 95.2 | 42.9 | 52.4 |

Same as a classmate's within 1-2 cases (one case = 4.8 points). `base` is lowest; `cot` and `cwe_hint` are highest."""
def strategy(n, key, title, desc, file, run_name, sample):
    return [
        md(f"## Step 4{n}: Strategy {key[1]}, {title} (24 pts)\n{desc}"),
        wf(f"{file}.py", sol(file) if SOLUTION else tmpl(file)),
        code(f"!python generate.py --methods {run_name} --redo --out ../results/run.jsonl\n!python evaluate.py ../results/run.jsonl --show base cot {run_name}"),
        answer(f"Strategy {key[1]}: {title}", 24, STRAT_HINT, sample),
    ]

cells = [
md("""# Lab: Prompting Strategies for Secure Code Generation
**Before you start:** `Runtime → Change runtime type → T4 GPU`, then run the cells **top to bottom**.

You will measure how the *prompt* changes the security of code written by a small LLM (**Qwen3-1.7B**) on
**SecurityEval** (Hugging Face `s2e-lab/SecurityEval`, 21 Python tasks with known CWEs), scored automatically by **Bandit**,
a static security analyser. The main job is to **design four different prompting strategies yourself**.

**What you have to do in this notebook**
* Run every cell in order (nothing to install by hand).
* **Write code in the four "Step 4" cells only** (`s1_role.py`, `s2_fewshot.py`, `s3_structured.py`, `s4_two_stage.py`), one per strategy. Each strategy is worth 24 points, with partial credit for the process.
* **Write your answers in the cells titled "✏️ YOUR ANSWER"** (double-click to edit).
* Submit this notebook **with its outputs** (File → Download .ipynb).

| Step | What | Points | Time |
|---|---|---|---|
| 0 | Setup + write files | | 1 min |
| 1 | Quick check (1 case) | | 1-2 min |
| 2 | Run the 7 provided methods | | 10-20 min |
| 3 | Scores, per-CWE table → answer **Task 1** (setup check) | 4 | 5 min |
| 3b | Helper: compare two methods on one case | | as needed |
| 4a-4d | **Your four prompting strategies** | 96 (4 × 24) | 15-40 min |"""),
code("""!pip -q install bandit==1.9.4
import os, torch
assert torch.cuda.is_available(), "No GPU! Runtime > Change runtime type > T4 GPU, then run this cell again."
print("GPU:", torch.cuda.get_device_name(0))
for d in ("lab", "data", "results"): os.makedirs(f"/content/lab_work/{d}", exist_ok=True)
os.chdir("/content/lab_work/lab"); print("working dir:", os.getcwd())
import sys; sys.path.insert(0, os.getcwd())  # so `import scorer` works in later cells"""),
md("### Files (do not edit these; you write your strategies in Step 4)"),
wf("scorer.py", read("scorer.py")), wf("prompts.py", read("prompts.py")),
wf("generate.py", read("generate.py")), wf("evaluate.py", read("evaluate.py")), wf("audit.py", read("audit.py")),
wf("../data/cases.jsonl", open(os.path.join(ROOT, "data", "cases.jsonl")).read()),
md("""## Step 1: quick check (one case, `base` method)
If this prints a one-row table, your setup works. The first run downloads the model (~3.5 GB, 1-3 min)."""),
code("""!python generate.py --limit 1 --methods base --out ../results/check.jsonl
!python evaluate.py ../results/check.jsonl"""),
md("""## Step 2: run the provided methods
Methods: `base`, `sec_instruct`, `few_shot`, `cot`, `cot_fewshot`, `cwe_hint` (oracle upper bound), `self_refine`.
It saves after every method, so if the session disconnects, re-run this cell and it **resumes**."""),
code("!python generate.py --out ../results/run.jsonl"),
md("""## Step 3: scores
Columns: `valid%` parses as Python · `func%` defines the requested function · `vuln%` Bandit finds the target CWE ·
**`SECURE%`** = valid, has the function, and no target-CWE finding.
Greedy decoding is used, but different GPUs/versions can differ by a case or two; each case is ≈ 4.8 points.
The second table shows, for every CWE, how many cases are secure per method (`secure/total`): useful to see which vulnerability types a strategy helps."""),
code("!python evaluate.py ../results/run.jsonl"),
answer("Task 1: setup check", 4,
       "Paste your score table below (copy the text output above). You are not graded on the numbers; this shows that your setup works. Optionally say which provided method looks best and worst.", S_TASK1),
md("### Reliability check (optional): truncated outputs, unparsable code"),
code("!python audit.py ../results/run.jsonl"),
md("""## Step 3b: helper, compare two methods on one case
Pick a `CASE` (an id from the per-CWE table: e.g. `CWE-078_author_1.py`) and two methods `A` and `B`. The cell prints each method's code and Bandit's findings.
Change the three variables and re-run as often as you like. Use it with your own strategies (`"s1_role"`, ...) to see *why* a score changed."""),
code("""import json
from scorer import bandit_cwes
CASE = "CWE-078_author_1.py"      # <- change me (any case id)
A, B = "base", "cot"              # <- change me (any two methods, e.g. "base" and "s3_structured")
rows = {(r["id"], r["method"]): r for r in map(json.loads, open("../results/run.jsonl"))}
print("available cases:", sorted({k[0] for k in rows}))
for m in (A, B):
    r = rows[(CASE, m)]
    print("=" * 70); print(f"method = {m}    case = {CASE}"); print(r["code"])
    try:
        cwes, findings = bandit_cwes(r["code"])
        print("\\nBandit CWEs:", sorted(cwes))
        for f in findings: print("  ", f["test_id"], f["issue_severity"], "-", f["issue_text"])
    except SyntaxError as e:
        print("\\n(this code does not parse:", e.msg, ")")"""),
md("""## Step 4: design your own prompting strategies (96 pts)
Four strategies, **24 points each**, each in its own cell and its own answer block. You can do them in any order, and a strategy that does not beat `base` still earns the process points.
For every strategy:
1. edit the template cell (it overwrites the strategy file); the template starts as a copy of `base`;
2. run the cell below it (generates, then scores your strategy next to `base` and `cot`);
3. **try at least 2 versions**: edit, re-run (`--redo` replaces the old result), and write down what changed and how the score moved;
4. fill in the ✏️ answer cell.

Rules, checked automatically: a strategy may use `c["prompt"]` only. If anything else changes from case to case (e.g. `c["cwe"]`, the answer key), `generate.py` refuses to run. Do not paste benchmark tasks into your prompt.
Tip: one case = 4.8 points; the whole run of a strategy takes about 30-150 seconds."""),
*strategy("a", "s1", "role / system prompt",
          "Change **only the system prompt** (who the model is told to be, what it values and must never do). The user message stays as in `base`, so the whole effect comes from the role.",
          "s1_role", "s1_role", S1),
*strategy("b", "s2", "few-shot with your own examples",
          "Write **at least 2 demonstrations** (task stub, secure completion) about functions that are **not** in the benchmark. Which vulnerability types do your demos cover, and does a demo about X help on a task about Y?",
          "s2_fewshot", "s2_fewshot", S2),
*strategy("c", "s3", "structured reasoning or checklist",
          "Give the model a **scaffold to follow before it writes code**: a security checklist, a step-by-step recipe, a threat-to-mitigation table. Long prompts can hurt a 1.7B model; compare shorter and longer scaffolds.",
          "s3_structured", "s3_structured", S3),
*strategy("d", "s4", "two-stage prompting",
          "The model is called **twice**: stage 1 (`s4_two_stage`) and stage 2 (`s4_two_stage_stage2`), which sees stage 1's answer. Stage 2's code is scored. E.g. plan then code, or draft then a *specific* review. It must differ from the built-in `self_refine`. Takes about twice as long.",
          "s4_two_stage", "s4_two_stage", S4),
md("### Save your results\nDownload `run.jsonl` and `run.scores.json` (Colab deletes files when the session ends). Also download this notebook **with outputs**: File → Download → .ipynb."),
code("""try:
    from google.colab import files
    for f in ("../results/run.jsonl", "../results/run.scores.json"): files.download(f)
except ImportError:
    print("Not on Colab; files are in", os.path.abspath("../results"))"""),
]
for n, c in enumerate(cells): c["id"] = f"cell{n:03d}"  # nbformat >= 5.1 requires cell ids
nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"provenance": [], "gpuType": "T4"},
      "kernelspec": {"name": "python3", "display_name": "Python 3"}}, "nbformat": 4, "nbformat_minor": 5}
out = os.path.join(ROOT, "instructor", "secure_codegen_lab_SOLUTION.ipynb") if SOLUTION else os.path.join(ROOT, "student", "secure_codegen_lab.ipynb")
json.dump(nb, open(out, "w"), indent=1); print("wrote", out, f"({len(cells)} cells)")
