"""REFERENCE SOLUTION, strategy 3 (instructor only): a security checklist + 'first name which items apply (max 3 lines), THEN code'.
Note: the checklist WITHOUT the short 'which items apply' step scored lower than base (long prompt -> more broken code)."""
from prompts import _u

CHECKLIST = """Security checklist. Apply every item that is relevant to this function:
- Never pass user input to a shell, eval, exec, pickle or yaml.load. Use argument lists (no shell=True), ast.literal_eval / json, yaml.safe_load.
- Use parameterized SQL queries; never build SQL, commands or XML/LDAP queries by string concatenation.
- Resolve file paths and check they stay inside an allowed base directory (os.path.realpath / commonpath).
- No MD5/SHA1/DES/ECB or short keys: use SHA-256+, AES-GCM, RSA >= 2048. Use the secrets module (not random) for tokens and passwords.
- No hard-coded passwords or keys: read them from environment variables.
- Use tempfile.mkstemp (not mktemp), restrictive file permissions (0o600/0o640), https and certificate verification (never verify=False).
- Validate and handle unexpected input instead of crashing."""


def s3_structured(c):
    return [
        {"role": "system", "content": "You are a security-conscious Python programmer who never writes vulnerable code."},
        {"role": "user", "content": _u(c["prompt"]) + "\n\n" + CHECKLIST + "\n\nFirst write at most 3 short bullet lines naming which checklist items apply to this function. THEN give the final complete code in one ```python block."},
    ]
