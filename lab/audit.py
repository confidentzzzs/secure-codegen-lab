"""Reliability audit of a results file (not about performance).
Usage: python audit.py results/run.jsonl [--model Qwen/Qwen3.5-2B] [--max-tokens 1280]
Reports, per method and overall:
  TRUNCATION : generation hit the token budget (or fence left open)
  PARSER     : no code fence / fence left inside extracted code / extracted code not valid Python
  HARNESS    : script crashed or timed out (no verdict), plus per-test failure reasons
               (wrong_result, unexpected_exception:<Type>, no_exception_raised, ...)"""
import argparse, ast, collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scorer import bandit_cwes

ap = argparse.ArgumentParser(); ap.add_argument("results"); ap.add_argument("--cases", default="../data/cases.jsonl")
ap.add_argument("--model", default=None); ap.add_argument("--max-tokens", type=int, default=2048)
a = ap.parse_args()
cases = {c["id"]: c for c in map(json.loads, open(a.cases))}
rows = [json.loads(l) for l in open(a.results)]
tok = None
if a.model:
    from transformers import AutoTokenizer; tok = AutoTokenizer.from_pretrained(a.model)

S = collections.defaultdict(collections.Counter); reasons = collections.defaultdict(collections.Counter)
examples = collections.defaultdict(list)
for r in rows:
    m, s, c = r["method"], None, cases[r["id"]]; s = S[m]; s["n"] += 1
    raw, code = r["raw"], r["code"]
    # --- truncation
    if "truncated" in r: trunc = r["truncated"]
    elif tok: trunc = len(tok(raw)["input_ids"]) >= a.max_tokens - 1
    else: trunc = False
    open_fence = raw.count("```") % 2 == 1
    if trunc: s["truncated"] += 1; examples["truncated"].append((m, r["id"]))
    if open_fence: s["unclosed_fence"] += 1
    # --- parser
    if "```" not in raw: s["no_fence_in_raw"] += 1
    if "```" in code: s["fence_left_in_code"] += 1; examples["fence_left"].append((m, r["id"]))
    try: ast.parse(code); parses = True
    except SyntaxError as e:
        parses = False; s["syntax_error"] += 1
        s["syntax_error_and_truncated"] += bool(trunc or open_fence)
        examples["syntax"].append((m, r["id"], f"line {e.lineno}: {(e.text or '').strip()[:60]}"))
    if c['func'] and f"def {c['func']}" not in code: s["target_func_missing"] += 1
    # --- scorer / harness
    if "testcases" in c:  # SecCodePLT: executable tests
        from testrunner import run_tests
        res = run_tests(c["setup"], code, c["testcases"], c["func"])
        if "error" in res:
            s["harness_no_verdict"] += 1; reasons[m][res["error"][:70]] += 1
            if res["error"] == "timeout": s["harness_timeout"] += 1
        else:
            s["harness_ok"] += 1
            for w in res.get("why", []): reasons[m][w] += 1
            if any(w.startswith("unexpected_exception") for w in res.get("why", [])): s["samples_with_unexpected_exception"] += 1
    else:  # SecurityEval: Bandit. A crash/timeout of Bandit itself would show up as an exception here.
        if not parses: s["harness_no_verdict"] += 1; reasons[m]["code does not parse (Bandit not run)"] += 1
        else:
            try:
                cw, _ = bandit_cwes(code); s["harness_ok"] += 1
                reasons[m]["target CWE flagged" if c["cwe"] in cw else "target CWE not flagged"] += 1
            except Exception as e:
                s["bandit_crash"] += 1; reasons[m]["bandit crash: " + str(e)[:50]] += 1

keys = ["n","truncated","unclosed_fence","no_fence_in_raw","fence_left_in_code","syntax_error","syntax_error_and_truncated",
        "target_func_missing","harness_ok","harness_no_verdict","harness_timeout","bandit_crash","samples_with_unexpected_exception"]
print(f"{'':36s}" + "".join(f"{m[:11]:>12s}" for m in S) + f"{'TOTAL':>10s}")
for k in keys:
    print(f"{k:36s}" + "".join(f"{S[m][k]:12d}" for m in S) + f"{sum(S[m][k] for m in S):10d}")
tot = collections.Counter()
for m in reasons: tot.update(reasons[m])
print("\nPer-test outcomes / harness errors (all methods):")
for k, v in tot.most_common(14): print(f"  {v:5d}  {k}")
for name, ex in examples.items():
    print(f"\nexamples of {name} ({len(ex)}):", ex[:4])
