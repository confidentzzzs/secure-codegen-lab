"""Build data/cases_v2.jsonl from SecCodePLT (Virtue-AI-HUB/SecCodePLT, Hugging Face).
A case is kept only if the benchmark's own reference solutions behave as expected under its tests:
  patched code    -> passes ALL capability and safety tests
  vulnerable code -> passes capability but FAILS at least one safety test
Then take up to PER_CWE cases per CWE for diversity."""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from testrunner import run_tests, verdict

PER_CWE = int(sys.argv[1]) if len(sys.argv) > 1 else 2
SRC, DST = "../data/seccodeplt/insecure_coding.parquet", os.environ.get("OUT", "../data/cases_v2.jsonl")
if not os.path.exists(SRC):
    import shutil
    from huggingface_hub import hf_hub_download
    os.makedirs("../data/seccodeplt", exist_ok=True)
    shutil.copy(hf_hub_download("Virtue-AI-HUB/SecCodePLT", "data/insecure_coding-00000-of-00001.parquet", repo_type="dataset"), SRC)
import pandas as pd
df = pd.read_parquet(SRC)

import ast
def predefined_names(setup):
    names = []
    for n in ast.parse(setup).body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)): names.append(n.name)
        elif isinstance(n, ast.Assign): names += [t.id for t in n.targets if isinstance(t, ast.Name)]
        elif isinstance(n, (ast.Import, ast.ImportFrom)): names += [(a.asname or a.name).split(".")[0] for a in n.names]
    return [x for x in dict.fromkeys(names) if not x.startswith("_") and x != "testcases"]

def stub(td, gt, setup):
    m = re.search(r"^(?:async\s+)?def\s+\w+\s*\(.*?\)\s*(?:->\s*[^:]+)?:\s*$", gt["code_before"], re.S | re.M)
    sig = m.group(0) if m else f"def {td['function_name']}(...):"
    ctx = ""
    lines = [l.strip().lstrip("-").strip() for l in (td.get("context") or "").strip().splitlines() if l.strip()]
    pre = predefined_names(setup)
    if pre:  # the tests define these globals; the task text often omits them, so name them (names only, no values)
        lines.append("Predefined globals available to your code: " + ", ".join(pre))
    if lines:  # every line must be a comment, or the prompt is invalid Python
        ctx = "# Context (already defined in the environment; do NOT redefine these):\n" + "\n".join("#   " + l for l in lines) + "\n\n"
    doc = [td["description"].strip(), "", "Args:", td["arguments"], "", "Returns:", td["return"]]
    if td.get("raise"): doc += ["", "Raises:", td["raise"]]
    doc = "\n".join(x for x in doc).replace("'''", '"""')
    head = gt["code_before"][:m.start()] if m else ""
    imports = "\n".join(l for l in head.splitlines() if l.startswith(("import ", "from ")))
    return (imports + "\n\n" if imports else "") + ctx + sig + "\n    '''\n    " + doc.replace("\n", "\n    ") + "\n    '''"

import builtins
def inconsistent(td, setup):
    text = " ".join(str(td.get(k, "")) for k in ("description", "context", "arguments", "return", "raise"))
    caps = set(re.findall(r"\b[A-Z][A-Z0-9]*_[A-Z0-9_]+\b", text))
    return sorted(c for c in caps if c not in setup)  # constants the text names that the tests never define

cases, tried, dropped = [], collections.Counter(), []
for _, r in df.iterrows():
    ut, gt, td = r["unittest"], r["ground_truth"], r["task_description"]
    if not ut["testcases"]: continue
    cwe = int(r["CWE_ID"])
    if tried[cwe] >= int(os.environ.get('BUDGET', PER_CWE * 4)): continue  # verification budget per CWE
    fn = td["function_name"]
    pat = gt["code_before"] + gt["patched_code"] + gt["code_after"]
    vul = gt["code_before"] + gt["vulnerable_code"] + gt["code_after"]
    bad_names = inconsistent(td, ut["setup"])
    if bad_names: dropped.append((r["id"], bad_names)); continue
    tried[cwe] += 1
    vp = verdict(run_tests(ut["setup"], pat, ut["testcases"], fn))
    vv = verdict(run_tests(ut["setup"], vul, ut["testcases"], fn))
    if vp["secure"] and vv["cap"] and not vv["safe"]:
        cases.append({"id": f"scp_{r['id']}", "cwe": cwe, "func": fn, "prompt": stub(td, gt, ut["setup"]),
                      "setup": ut["setup"], "testcases": ut["testcases"], "policy": td.get("security_policy", "")})
MAXN = int(os.environ.get('MAXN', 30))
final, cnt = [], collections.Counter()
for rnd in range(PER_CWE):  # round-robin: first case of every CWE, then second, ... up to MAXN
    seen = collections.Counter()
    for c in cases:
        seen[c["cwe"]] += 1
        if seen[c["cwe"]] == rnd + 1 and len(final) < MAXN: final.append(c); cnt[c["cwe"]] += 1
with open(DST, "w") as f:
    for c in final: f.write(json.dumps(c) + "\n")
print("dropped (task text names constants the tests do not define):", dropped)
print(f"verified {len(cases)} cases; kept {len(final)} over {len(cnt)} CWEs: {dict(sorted(cnt.items()))}")
