"""
Content injection/substitution engine for NEON-SHIELD.

Replaces the old hardcoded "images only" logic with a small, extensible list
of rules. Each rule is (matcher_fn, transform_fn, name). The first matching
rule wins. Add new rules by appending to RULES.
"""
import os
import sys

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")

REPLACEMENT_IMAGE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "local_images", "rax_logo.png"
)

try:
    with open(REPLACEMENT_IMAGE_PATH, "rb") as f:
        REPLACEMENT_IMAGE_DATA = f.read()
    print(f"[Rules] Loaded replacement image ({len(REPLACEMENT_IMAGE_DATA)} bytes).")
except Exception as e:
    print(f"[Error] Failed to load replacement image from {REPLACEMENT_IMAGE_PATH}: {e}")
    sys.exit(1)

BANNER_HTML = (
    b'<div style="position:fixed;bottom:0;left:0;right:0;z-index:2147483647;'
    b'background:#0f172a;color:#39ff14;font-family:monospace;font-size:13px;'
    b'padding:6px 12px;border-top:2px solid #39ff14;opacity:0.94;">'
    b"\xe2\x9a\xa1 NEON-SHIELD LAB: this page's traffic is being intercepted for an "
    b"authorized security research demo.</div>"
)


def is_image_body(body):
    """Detects if the response body starts with common image magic bytes."""
    if len(body) < 4:
        return False
    if body.startswith(b"\x89PNG"):
        return True
    if body.startswith(b"\xff\xd8\xff"):
        return True
    if body.startswith(b"GIF87") or body.startswith(b"GIF89"):
        return True
    if body.startswith(b"RIFF") and len(body) >= 12 and body[8:12] == b"WEBP":
        return True
    return False


def _parse_headers(header_lines):
    headers = {}
    for line in header_lines[1:]:
        if b":" in line:
            name, value = line.split(b":", 1)
            headers[name.strip().lower()] = value.strip()
    return headers


def _is_image_response(headers, request_path, body):
    content_type = headers.get(b"content-type", b"").decode("utf-8", errors="ignore").lower()
    if "image/" in content_type:
        return True, content_type
    if any(ext in request_path.lower() for ext in IMAGE_EXTS):
        return True, content_type
    if is_image_body(body):
        return True, content_type
    return False, content_type


def _build_image_replacement():
    new_headers = [
        b"HTTP/1.1 200 OK",
        b"Content-Type: image/png",
        f"Content-Length: {len(REPLACEMENT_IMAGE_DATA)}".encode("utf-8"),
        b"Connection: close",
        b"Cache-Control: no-store, no-cache, must-revalidate, max-age=0",
        b"Pragma: no-cache",
        b"Expires: 0",
        b"Server: NeonShieldLab/1.0",
    ]
    return b"\r\n".join(new_headers) + b"\r\n\r\n" + REPLACEMENT_IMAGE_DATA


def _inject_banner(header_lines, headers, body):
    content_type = headers.get(b"content-type", b"").decode("utf-8", errors="ignore").lower()
    if "text/html" not in content_type:
        return None
    content_encoding = headers.get(b"content-encoding", b"").decode("utf-8", errors="ignore").lower()
    if content_encoding and content_encoding != "identity":
        # Body is compressed (gzip/br/etc) -- we forced Accept-Encoding: identity
        # upstream, but some servers ignore that. Don't risk corrupting it.
        return None

    lower_body = body.lower()
    if b"</body>" in lower_body:
        idx = lower_body.rfind(b"</body>")
        new_body = body[:idx] + BANNER_HTML + body[idx:]
    elif b"</html>" in lower_body:
        idx = lower_body.rfind(b"</html>")
        new_body = body[:idx] + BANNER_HTML + body[idx:]
    else:
        return None

    new_header_lines = [header_lines[0]]
    replaced_length = False
    for line in header_lines[1:]:
        if line.lower().startswith(b"content-length:"):
            new_header_lines.append(f"Content-Length: {len(new_body)}".encode("utf-8"))
            replaced_length = True
        else:
            new_header_lines.append(line)
    if not replaced_length:
        new_header_lines.append(f"Content-Length: {len(new_body)}".encode("utf-8"))

    return b"\r\n".join(new_header_lines) + b"\r\n\r\n" + new_body


def apply_content_rules(response_bytes, request_path):
    """
    Inspects a raw upstream HTTP response and applies the first matching
    transformation rule. Returns (possibly_modified_response_bytes, rule_name_or_None).
    """
    header_end = response_bytes.find(b"\r\n\r\n")
    if header_end == -1:
        return response_bytes, None

    header_part = response_bytes[:header_end]
    body_part = response_bytes[header_end + 4:]
    header_lines = header_part.split(b"\r\n")
    headers = _parse_headers(header_lines)

    is_image, content_type = _is_image_response(headers, request_path, body_part)
    if is_image:
        print(f"[Rules] image-swap matched ({content_type or 'magic-bytes'}) for {request_path}")
        return _build_image_replacement(), "image-swap"

    injected = _inject_banner(header_lines, headers, body_part)
    if injected is not None:
        print(f"[Rules] html-banner matched for {request_path}")
        return injected, "html-banner"

    return response_bytes, None


def parse_response_meta(response_bytes):
    """Returns (status_code, content_type, body_length) for traffic logging."""
    header_end = response_bytes.find(b"\r\n\r\n")
    if header_end == -1:
        return "?", "-", len(response_bytes)

    header_part = response_bytes[:header_end]
    header_lines = header_part.split(b"\r\n")
    status_line = header_lines[0].decode("utf-8", errors="ignore")
    status_parts = status_line.split()
    status_code = status_parts[1] if len(status_parts) > 1 else "?"

    content_type = "-"
    for line in header_lines[1:]:
        if line.lower().startswith(b"content-type:"):
            content_type = line.split(b":", 1)[1].strip().decode("utf-8", errors="ignore")
            break

    return status_code, content_type, len(response_bytes) - header_end - 4
