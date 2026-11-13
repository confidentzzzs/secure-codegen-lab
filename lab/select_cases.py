"""Build data/cases.jsonl: SecurityEval cases whose reference insecure code Bandit flags with the labelled CWE.
This guarantees every case is automatically scorable."""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from scorer import bandit_cwes

SRC, DST = "../data/securityeval_full.jsonl", "../data/cases.jsonl"
if not os.path.exists(SRC):  # download from Hugging Face
    import shutil
    from huggingface_hub import hf_hub_download
    os.makedirs("../data", exist_ok=True)
    shutil.copy(hf_hub_download("s2e-lab/SecurityEval", "dataset.jsonl", repo_type="dataset"), SRC)
out = []
for l in open(SRC):
    r = json.loads(l)
    cwe = int(r["ID"].split("_")[0].split("-")[1])
    try:
        found, _ = bandit_cwes(r["Insecure_code"])
    except Exception:
        continue
    if cwe in found:
        m = re.search(r"def\s+(\w+)\s*\(", r["Prompt"])
        out.append({"id": r["ID"], "cwe": cwe, "prompt": r["Prompt"],
                    "func": m.group(1) if m else None})
with open(DST, "w") as f:
    for o in out: f.write(json.dumps(o) + "\n")
print(f"{len(out)} cases -> {DST}")
