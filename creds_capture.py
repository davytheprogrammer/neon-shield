"""
Credential-capture helpers for NEON-SHIELD.

Demonstrates -- for your own authorized test accounts/devices only -- why
plaintext HTTP and untrusted TLS interception are dangerous: it looks for
HTTP Basic Auth headers and plaintext login form submissions in decrypted
requests. Findings are only ever handed back to the caller in-process; this
module never writes to disk or the network itself (the caller decides where,
per traffic_log.py, which is local-only by design).
"""
import base64
import urllib.parse

CREDENTIAL_FIELD_HINTS = (
    "pass", "pwd", "passwd", "user", "uname", "login", "email", "account",
)


def _get_header(header_lines, name):
    prefix = (name + ":").lower()
    for line in header_lines:
        line_str = line.decode("utf-8", errors="ignore") if isinstance(line, bytes) else line
        if line_str.lower().startswith(prefix):
            return line_str.split(":", 1)[1].strip()
    return None


def _extract_basic_auth(header_lines):
    auth = _get_header(header_lines, "authorization")
    if not auth or not auth.lower().startswith("basic "):
        return None
    try:
        decoded = base64.b64decode(auth[6:].strip()).decode("utf-8", errors="ignore")
    except Exception:
        return None
    if ":" not in decoded:
        return None
    username, _, password = decoded.partition(":")
    return {"type": "http_basic_auth", "username": username, "password": password}


def _extract_form_submission(header_lines, body):
    if not body:
        return None
    content_type = _get_header(header_lines, "content-type") or ""
    if "application/x-www-form-urlencoded" not in content_type.lower():
        return None
    try:
        text = body.decode("utf-8", errors="ignore")
    except Exception:
        return None

    fields = urllib.parse.parse_qsl(text, keep_blank_values=True)
    if not fields:
        return None

    interesting = {k: v for k, v in fields if any(hint in k.lower() for hint in CREDENTIAL_FIELD_HINTS)}
    if not interesting:
        return None
    return {"type": "form_submission", "fields": interesting}


def capture_credentials(header_lines, body):
    """Returns a list of finding dicts (possibly empty) for a single request."""
    findings = []
    basic_auth = _extract_basic_auth(header_lines)
    if basic_auth:
        findings.append(basic_auth)
    form_submission = _extract_form_submission(header_lines, body)
    if form_submission:
        findings.append(form_submission)
    return findings
