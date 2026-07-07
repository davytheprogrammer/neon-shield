# ⚡ NEON-SHIELD // MITM Proxy Lab

```
   _  _ ___ ___  _  _    ___ _  _ ___ ___ _    ___
   |\ | |__ |  \ |\ | __  |  |__| |__ |__ |    |  \
   | \| |___|__/ | \|     |  |  | |___|___|___ |__/
   
      [!] INTERCEPT // INSPECT // TRANSFORM 
```

**NEON-SHIELD is a powerful, all-in-one MITM proxy for authorized security research & education only.** It demonstrates real-world network attack surfaces and why modern security (HTTPS, certificate pinning, network segmentation) matters by performing active Man-in-the-Middle attacks in a controlled lab environment.

---

## 🛑 DISCLAIMER — READ BEFORE USE

**THIS IS AN AUTHORIZED-USE-ONLY TOOL. UNAUTHORIZED USE IS ILLEGAL.**

NEON-SHIELD performs active MITM attacks that are **federal crimes without explicit authorization**:
- **ARP spoofing** to intercept traffic from devices on your network
- **TLS decryption** to read "secure" HTTPS traffic
- **Credential capture** to log passwords/auth tokens
- **DNS spoofing** to redirect domains to fake sites
- **Content injection** to modify web pages in-transit
- **Full traffic inspection & logging**

By using this tool, you confirm:

1. **Every device you target is owned by you OR you have explicit written authorization** from the owner/operator (e.g., a signed penetration-test agreement).
2. **Every network you run this on is authorized for testing** (your home lab, a corporate lab with permission, a CTF competition, etc.).
3. **You understand the legal consequences:** unauthorized wiretapping, computer fraud, unauthorized access, and privacy violations in most jurisdictions carry **felony charges, fines, and imprisonment.**
4. **This tool is for EDUCATION & AUTHORIZED SECURITY RESEARCH**, not for:
   - Spying on roommates, coworkers, or anyone without consent
   - Stealing credentials from others' accounts
   - Breaking into systems you don't own or aren't authorized to test
   - Selling/distributing captured data
   - Bypassing security to commit fraud

**If you're unsure whether you're authorized, DO NOT RUN THIS TOOL.** When in doubt, ask a lawyer or your organization's security team.

---

## 🌌 CAPABILITIES

NEON-SHIELD is a complete MITM toolkit for demonstrating real attacks:

### Core Interception
- **Automatic ARP Spoofing:** Routes target devices' traffic through this host with zero configuration on the target devices.
- **Transparent HTTP/HTTPS Redirect:** iptables rules transparently intercept plain-text and encrypted traffic without needing manual proxy settings.
- **On-The-Fly TLS Decryption:** Generates domain certificates signed by a local Root CA, allowing inspection of "secure" connections.

### Content Manipulation
- **Image Replacement:** Automatically swap images with a custom payload (default: RAX logo, configurable).
- **HTML Banner Injection:** Inject a visible warning banner into HTML pages to demonstrate in-browser exploitation vectors.
- **Extensible Rule Engine:** Add custom content transformation rules (swap videos, modify JSON APIs, rewrite forms, etc.).

### Traffic Intelligence
- **Live Traffic Inspector:** Every HTTP/HTTPS request is logged with method, domain, path, status code, content-type, size, and source IP.
- **Loopback-Only Control Panel:** View live traffic and captured data in a secure web dashboard (localhost-only, not exposed to the LAN).
- **Optional Local File Logging:** All events can be appended to a local JSON log file for post-lab review.

### Credential Capture (Educational Demo)
- **HTTP Basic Auth Extraction:** Automatically captures plaintext `Authorization: Basic` headers.
- **Login Form Interception:** Detects form submissions and captures password/credential field values.
- **Local-Only Storage:** Credentials are logged to the local machine ONLY (never sent anywhere else). Demonstrates why HTTPS is critical.

### Network Manipulation
- **Scoped DNS Spoofing:** Redirect only explicitly-named domains to a local IP (e.g., `example.com → 192.168.1.1`). Everything else is forwarded untouched to the real DNS server. Cannot be used for blanket DNS hijacking.

---

## 🛠️ ARCHITECTURE

The tool is modular and designed for extensibility:

- **`proxy.py`**: Main engine. Auto-mode only (no manual proxy mode). Orchestrates ARP spoofing, iptables rules, and runs all listeners (transparent HTTP/HTTPS, LAN dashboard, loopback control panel, DNS spoofer).
- **`netdiscover.py`**: ARP-scans the local subnet to enumerate live devices.
- **`arpspoof.py`**: Continuous bidirectional ARP poisoning with clean restoration on exit.
- **`iptables_ctl.py`**: Enables IP forwarding and manages the NAT REDIRECT rules for transparent interception (HTTP/HTTPS/DNS).
- **`content_rules.py`**: Pluggable rule engine for modifying responses. Image replacement, HTML banner injection, etc.
- **`creds_capture.py`**: Extracts credentials from HTTP Basic Auth headers and form submissions.
- **`traffic_log.py`**: Thread-safe in-memory log with optional local file append.
- **`dns_spoof.py`**: Scoped DNS spoofing (allow-list only, not blanket hijacking).
- **`ca.py`**: Certificate Authority engine. Generates on-the-fly domain certs signed by a local Root CA.
- **`dashboard.html`**: LAN-facing dashboard (http://proxy-ip:8080) for CA download and zero-config explainer.
- **`control_panel.html`**: Loopback-only control panel (http://127.0.0.1:7070) for live traffic/credential inspection.

---

## 💻 QUICKSTART

NEON-SHIELD is designed to "just work" on your lab network with a single command.

### 1. Clone & Install

```bash
git clone <this-repo>
cd neon-shield
pip install -r requirements.txt  # Installs: cryptography, scapy
```

### 2. Confirm Authorization

```bash
sudo python3 proxy.py
```

The tool will print a large authorization banner and require you to type `YES I UNDERSTAND` to confirm you're authorized. If you're not sure, **do not proceed.**

### 3. Access the Interfaces

Once running:

- **LAN Dashboard (device CA trust):** `http://<your-host-ip>:8080/`
  - Download the Root CA certificate
  - View device-specific trust instructions (iOS, Android, Windows, Linux, macOS)
  
- **Control Panel (traffic inspection, credentials):** `http://127.0.0.1:7070/` (localhost only)
  - Live traffic log (every intercepted HTTP/HTTPS request)
  - Captured credentials log (if any login forms/basic auth encountered)
  
- **Press Ctrl+C to stop:** Automatically restores ARP tables and removes firewall rules.

### Example: Intercept Specific Devices

```bash
# Only intercept 192.168.1.50 and 192.168.1.51
sudo python3 proxy.py --targets 192.168.1.50,192.168.1.51 -y
```

### Example: Add DNS Spoofing

```bash
# Also spoofs example.com to your host IP (demo phishing/captive portal)
sudo python3 proxy.py --dns-redirect "example.com:192.168.1.1" -y
```

### Example: Auto-Discover All Devices

```bash
# Scans the subnet for every live host except the gateway and this machine
sudo python3 proxy.py -y
```

---

## ⚠️ HOW IT WORKS (And Why It Matters)

Understanding the mechanisms helps you appreciate why modern security defenses exist:

### 1. ARP Spoofing

Devices on a LAN use ARP (Address Resolution Protocol) to map IP addresses to MAC addresses. Without ARP spoofing, your traffic goes directly to the gateway. NEON-SHIELD forges ARP replies claiming "I am the gateway at MAC address XX:XX:XX:..." — so all target devices route their traffic through this host instead. **Why it matters:** This is why switches support Dynamic ARP Inspection (DAI) and why encrypted VPNs work (they bypass the LAN entirely).

### 2. Transparent Redirect

With traffic now flowing through this host, iptables rules silently redirect:
- Port 80 (HTTP) → 8081 (transparent proxy)
- Port 443 (HTTPS) → 8443 (transparent proxy)
- Port 53 (DNS, optional) → 5353 (scoped DNS spoofer)

Devices never see a proxy setting — they believe they're talking directly to the destination. **Why it matters:** This is why VPNs and SOCKS proxies require client-side configuration (not vulnerable to transparent redirect), and why application-level proxies (like Burp Suite) need to be explicitly configured.

### 3. TLS Interception

When an intercepted device tries HTTPS, this host presents a fake certificate. If the device trusts NEON-SHIELD's Root CA (installed manually), the TLS handshake succeeds and the proxy reads the plaintext traffic. If the device **doesn't** trust the CA, the browser shows a big red warning.

**Critical detail:** NEON-SHIELD does NOT silently bypass HTTPS. It demonstrates why certificate validation warnings exist. If a device sees "Untrusted certificate," that's the security working as designed. **Why it matters:** This is why Public Key Pinning (PKP), certificate transparency, and hardware security tokens exist — they prevent even authorized administrators from MITM'ing encrypted traffic.

### 4. Content Modification & Credential Capture

Once traffic is decrypted, NEON-SHIELD can:
- Replace images, inject HTML banners, modify JSON responses
- Extract credentials from login forms and Basic Auth headers
- Log all activity to a local database

**Why it matters:** Plaintext HTTP has always been vulnerable to MITM content injection. HTTPS protects against this — unless the network itself is compromised or the user manually trusts a malicious CA.

### 5. DNS Spoofing

If enabled, NEON-SHIELD spoofs DNS replies for a configured set of domains (example: `example.com → 192.168.1.1`). Everything else is forwarded untouched to the real DNS server. **Why it matters:** Demonstrates how phishing infrastructure works, and why DNS-over-HTTPS (DoH) and DNSSEC exist.

---

## 🔐 STAYING SAFE (Defensive Strategies)

Understanding how NEON-SHIELD works highlights real defenses used in production:

| Attack Vector | Defense |
|---|---|
| **ARP Spoofing** | Dynamic ARP Inspection (DAI) on managed switches; VPN/encrypted tunnel (bypasses LAN) |
| **Transparent REDIRECT** | Explicitly-configured proxy (not transparent); SOCKS proxy; VPN |
| **TLS Interception** | Certificate pinning (mobile apps); HSTS preload; hardware security tokens; certificate transparency monitors |
| **Content Injection** | HTTPS everywhere; Content-Security-Policy (CSP) headers; Subresource Integrity (SRI) |
| **Credential Capture** | HTTPS-only authentication; OAuth 2.0 with token rotation; multi-factor authentication (MFA) |
| **DNS Spoofing** | DNSSEC validation; DNS-over-HTTPS (DoH); VPN/encrypted resolver |

---

## 📖 EDUCATIONAL VALUE

NEON-SHIELD is most valuable when used to:

1. **Demonstrate real attack surface:** Show students/colleagues why their device/network is vulnerable to MITM attacks on untrusted Wi-Fi.
2. **Test your defenses:** Run NEON-SHIELD against your own devices to verify that certificate pinning, HSTS, MFA, or network segmentation actually work.
3. **CTF / Capture the Flag:** Use as a proxy for CTF challenges that require MITM capabilities.
4. **Security training:** Authorized security training courses can use it to show attackers' perspective.
5. **Red team labs:** Signed penetration-test engagements.

**What it's NOT for:**
- Spying on friends, family, roommates, or coworkers
- Stealing passwords from others' accounts
- Breaking into systems you don't own
- Any use without explicit written authorization

---

## 🔧 ADVANCED: Extending NEON-SHIELD

The tool is designed for extensibility:

### Custom Content Rules

Edit `content_rules.py` to add new transformations. The `apply_content_rules()` function is called on every response. Example:

```python
# Add custom rule to replace all "foo" with "bar" in HTML
def _custom_replace(header_lines, headers, body):
    if "text/html" not in headers.get(b"content-type", b"").decode().lower():
        return None
    new_body = body.replace(b"foo", b"bar")
    # Rebuild headers, adjust Content-Length, return modified response
    ...
```

### Custom DNS Spoofing Map

Pass `--dns-redirect` with any domain:IP pairs:

```bash
sudo python3 proxy.py --dns-redirect "google.com:127.0.0.1,example.com:192.168.1.100" -y
```

### Custom CA Certificates

Generate your own Root CA for a custom organization name:

```bash
# Edit ca.py: change "EduLab Root CA" to your org name, re-run
python3 ca.py
```

### Custom Credential Capture

Edit `creds_capture.py` to detect additional auth schemes (OAuth tokens, JWT headers, API keys, etc.).

---

## 📝 REQUIREMENTS

- **OS:** Linux (uses iptables, raw sockets, ARP packet injection)
- **Root:** Required (iptables, ARP spoofing, port binding)
- **Python 3.8+**
- **Dependencies:** `cryptography`, `scapy` (see `requirements.txt`)

---

## 🚨 Troubleshooting

**"Error: ARP spoofing failed" / "MAC address not found"**
- The target device may not be on the network yet, or the interface name is wrong. Verify with `ip route show default`.

**"Permission denied" on iptables**
- Run with `sudo`. The tool requires root for ARP spoofing and firewall rules.

**"Certificate not trusted" on target device**
- Normal and expected. The device must manually download and install the NEON-SHIELD Root CA. See the LAN dashboard for device-specific instructions.

**Traffic not being intercepted**
- Verify the target device is on the same LAN (not on a different VLAN or remote network).
- Check that ARP spoofing is working: `arp -a` on the target should show this host's IP mapped to its real MAC.

**Control panel shows no traffic**
- Traffic is only logged for traffic that reaches the proxy. If the target device is using a VPN, DoH, or has pinned certificates, that traffic won't be visible.

---

## 📚 Further Reading

- [Why HTTPS matters](https://https.cio.gov/)
- [OWASP: Man-in-the-Middle (MITM) Attacks](https://owasp.org/www-community/attacks/Manipulator-in-the-middle_attack)
- [Public Key Pinning (HPKP & App-Level Pinning)](https://owasp.org/www-community/controls/Pinning)
- [DNS Security (DNSSEC, DoH, DoT)](https://en.wikipedia.org/wiki/DNS_security_extensions)
- [Certificate Transparency](https://certificate.transparency.dev/)
- [Network Segmentation & VLANs](https://en.wikipedia.org/wiki/Virtual_LAN)

---

## 📄 License

This project is provided as-is for educational and authorized security research purposes only. **Unauthorized use violates computer fraud and wiretapping laws.** See the disclaimer above. Use at your own risk.

---

**NEON-SHIELD: Demonstrating why network security and HTTPS matter.** 🔐
