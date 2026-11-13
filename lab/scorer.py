"""Automatic security scorer: runs Bandit on a code string and reports CWE findings."""
import ast, json, os, subprocess, sys, tempfile



# Bandit's "informational" checks fire on mere use/import of a module (e.g. `import subprocess`, list-form
# subprocess calls), even in safe code. They are not vulnerabilities, so we ignore them:
#   B401-B415 = import checks, B603 = subprocess without shell, B607 = partial executable path
NOISE = {f"B4{n:02d}" for n in range(1, 16)} | {"B603", "B607"}


def bandit_cwes(code: str):
    """Return (set_of_cwe_ids_as_int, list_of_findings). Raises SyntaxError if code does not parse."""
    ast.parse(code)  # validity gate
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "snippet.py")
        open(f, "w").write(code)
        r = subprocess.run([sys.executable, "-m", "bandit", "-q", "-f", "json", f], capture_output=True, text=True)
    out = json.loads(r.stdout or "{}")
    findings = [x for x in out.get("results", []) if x["test_id"] not in NOISE]
    return {x["issue_cwe"]["id"] for x in findings if x.get("issue_cwe")}, findings
