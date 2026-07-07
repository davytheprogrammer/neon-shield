# ⚡ NEON-SHIELD v2.0 — Advanced MITM Lab

> **EDUCATIONAL USE ONLY.** Authorized security research & pentesting demonstrations in controlled environments. Unauthorized MITM attacks are federal crimes.

```
   _  _ ___ ___  _  _    ___ _  _ ___ ___ _    ___
   |\ | |__ |  \ |\ | __  |  |__| |__ |__ |    |  \
   | \| |___|__/ | \|     |  |  | |___|___|___ |__/
   
      [!] INTERCEPT // INSPECT // TRANSFORM 
```

NEON-SHIELD is a **production-grade MITM proxy lab** for demonstrating real-world network vulnerabilities and why modern security (HTTPS, certificate pinning, VPNs, MFA, network segmentation) matters.

---

## 🛑 LEGAL DISCLAIMER

**UNAUTHORIZED USE OF THIS TOOL IS A FEDERAL CRIME.**

NEON-SHIELD performs active MITM attacks:
- **ARP spoofing** to intercept other devices' traffic
- **TLS decryption** to read HTTPS communications
- **Credential capture** to log passwords & auth tokens
- **DNS spoofing** to redirect domain names
- **Content injection** to modify web pages in-transit
- **Full traffic inspection & logging**

### By using this tool, you confirm:

✓ **Every device you intercept is owned by you OR you have explicit written authorization** from the owner/operator (e.g., a signed penetration-test agreement)  
✓ **This network is your own OR you're authorized to conduct security testing on it** (your home lab, corporate lab, CTF competition, authorized pentest engagement, etc.)  
✓ **You understand the legal consequences** of unauthorized use: felony charges (Computer Fraud & Abuse Act, Wiretap Act, Unauthorized Access), significant fines ($250k+), and imprisonment (up to 10+ years depending on jurisdiction)  
✓ **You understand this tool is strictly for EDUCATION & AUTHORIZED SECURITY RESEARCH**, not for:
- Spying on roommates, coworkers, family, or anyone without consent
- Stealing passwords or credentials from others' accounts  
- Breaking into systems you don't own or aren't authorized to test
- Selling or distributing captured data
- Any form of fraud, harassment, or malicious use

**If you're unsure whether you're authorized to use this tool on a specific network or device, DO NOT USE IT.** When in doubt, consult your organization's security team or a lawyer.

---

## ⚡ Key Features

### Zero-Config Auto Mode
- **Single command startup:** `sudo python3 main_cli.py start`
- **Auto-discovers** devices on your LAN
- **No per-device configuration** — ARP spoofing + transparent redirect handle everything
- **Interactive setup wizard** for first-time users

### Advanced MITM Capabilities
- **Traffic Inspector:** Every HTTP/HTTPS request logged with method, domain, path, status, size, source IP
- **Credential Capture:** Auto-extracts HTTP Basic Auth and login form submissions
- **Content Rules:** Image replacement, HTML banner injection, extensible framework
- **DNS Spoofing:** Scoped allow-list (only specified domains redirected)
- **Persistent Logging:** Optional local JSON file storage for post-lab review

### Robust & Production-Ready
- **Config file system** (YAML) — define everything once, reuse forever
- **Health monitoring** — background thread checks ARP/iptables health, auto-recovers failures
- **State management** — saves/restores state for crash recovery
- **Comprehensive logging** — structured logs with rotation (DEBUG/INFO/WARN/ERROR)
- **Dry-run mode** — validate config without actually spoofing
- **Emergency cleanup** — `cleanup.sh` script for disaster recovery
- **Systemd integration** — run as a service

### User-Friendly CLI
```bash
neon-shield init              # Interactive first-time setup
neon-shield start             # Start interception (auto-loads config)
neon-shield stop              # Stop & restore network
neon-shield status            # Check current status
neon-shield cleanup           # Emergency recovery
neon-shield test              # Validate config (dry-run)
```

### Beautiful Dashboards
- **LAN Dashboard** (http://proxy-ip:8080) — CA download, device trust guides
- **Control Panel** (http://127.0.0.1:7070, localhost-only) — live traffic & credentials inspection

---

## 📚 Why NEON-SHIELD Matters

Understanding how NEON-SHIELD works helps you appreciate why modern security defenses exist:

| Attack Vector | NEON-SHIELD Demonstrates | Real Defense |
|---|---|---|
| **ARP Spoofing** | Attacker redirects traffic through their machine | Dynamic ARP Inspection (DAI) on managed switches, VPNs |
| **Transparent Redirect** | Traffic silently funneled to proxy | Explicit proxy configuration, VPNs, SOCKS proxy |
| **TLS Interception** | HTTPS traffic decrypted after client trusts fake cert | Certificate pinning, HSTS preload, certificate transparency |
| **Credential Capture** | Passwords logged from login forms | HTTPS-only auth, OAuth 2.0, MFA, token rotation |
| **DNS Spoofing** | Fake domains redirect to attacker site | DNSSEC validation, DoH (DNS-over-HTTPS), VPNs |
| **Content Injection** | Malicious code injected into HTML pages | Content-Security-Policy (CSP), HTTPS, Subresource Integrity |

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/neon-shield.git
cd neon-shield
pip install -r requirements.txt
chmod +x cleanup.sh
```

### First Run

```bash
sudo python3 main_cli.py init
```

Interactive setup wizard asks you to:
- Confirm authorization (LEGAL!)
- Configure network interface & targets
- Enable/disable content rules & DNS spoofing
- Set logging preferences

Answers saved to `neon-shield.yml` for future runs.

### Start Interception

```bash
sudo python3 main_cli.py start
```

Then:
- **Download CA cert:** http://your-machine-ip:8080/ca.crt
- **Monitor traffic:** http://127.0.0.1:7070/ (localhost only)
- **Stop:** Press Ctrl+C (auto-restores network)

### Examples

```bash
# Specific targets
sudo python3 main_cli.py start --targets 192.168.1.50,192.168.1.51 -y

# With DNS spoofing
sudo python3 main_cli.py start --dns-redirect "example.com:192.168.1.1" -y

# Dry-run (validate without spoofing)
python3 main_cli.py test

# Emergency cleanup
sudo cleanup.sh
```

---

## 📖 Documentation

- **[SETUP.md](SETUP.md)** — Detailed setup guide, CLI reference, troubleshooting
- **[neon-shield.yml](neon-shield.yml)** — Configuration file template (all options documented)
- **CLI Help:** `python3 main_cli.py --help`

---

## 🏗️ Architecture

**Modular, extensible design:**

- **`main_cli.py`** — Click-based CLI with subcommands
- **`proxy.py`** — Core MITM engine (transparent HTTP/HTTPS/DNS handlers)
- **`config.py`** — YAML config loader & validator
- **`netdiscover.py`** — ARP-scan for host discovery
- **`arpspoof.py`** — Bidirectional ARP poisoning with graceful cleanup
- **`iptables_ctl.py`** — Transparent NAT redirect (optional DNS)
- **`content_rules.py`** — Pluggable response transformation (image swap, HTML injection)
- **`creds_capture.py`** — Extract credentials from HTTP Basic Auth & form submissions
- **`traffic_log.py`** — Thread-safe in-memory + optional file logging
- **`dns_spoof.py`** — Scoped DNS spoofing (allow-list only)
- **`health_monitor.py`** — Background health checks + auto-recovery
- **`state_manager.py`** — Crash recovery state files
- **`log_handler.py`** — Structured logging with rotation

---

## 🧪 For Penetration Testers

Example authorized pentest workflow:

```bash
# 1. Setup (tailored to client network)
sudo python3 main_cli.py init

# 2. Validate before going live
python3 main_cli.py test

# 3. Start interception
sudo python3 main_cli.py start -y

# 4. Monitor in real-time (another terminal)
open http://127.0.0.1:7070/

# 5. Review logs post-engagement
cat logs/traffic.jsonl
cat logs/credentials.jsonl

# 6. Clean up & restore network
sudo python3 main_cli.py stop
# OR
sudo cleanup.sh
```

Logs are in standard JSON lines format for easy parsing & reporting.

---

## 🛡️ Safety Features

- **Requires root** (ARP spoofing & iptables need root)
- **Confirms authorization** at startup (logged to audit file)
- **State recovery** — if daemon crashes, run `cleanup.sh` to restore
- **Health monitoring** — auto-detects & recovers from failed components
- **Local-only data** — all captured data stays on the proxy machine (no exfiltration)
- **Graceful shutdown** — Ctrl+C restores ARP tables & iptables rules

---

## 📊 Testing

```bash
# Run test suite
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

GitHub Actions automatically runs tests on every push/PR.

---

## 📝 Configuration Reference

See `neon-shield.yml` for all options:
- Network settings (interface, targets, gateway)
- Content rules (image swap, HTML banner)
- DNS spoofing (allow-list domains → IPs)
- Logging (level, file paths, rotation)
- Health monitoring (check interval, auto-recovery)
- Web interfaces (dashboard, control panel ports)

---

## 🤝 Contributing

Bug reports, feature requests, and PRs welcome! Please:
1. Confirm you understand the legal/ethical use policy
2. Add tests for new features
3. Update documentation

---

## 📄 License

MIT License. See `LICENSE` file.

**Disclaimer:** Users assume all legal responsibility for use of this tool. The authors assume no liability for unauthorized, illegal, or unethical use.

---

## 🎓 Educational Resources

- [OWASP: Man-in-the-Middle (MITM) Attacks](https://owasp.org/www-community/attacks/Manipulator-in-the-middle_attack)
- [Why HTTPS Matters](https://https.cio.gov/)
- [Certificate Pinning](https://owasp.org/www-community/controls/Pinning)
- [DNS Security (DNSSEC, DoH, DoT)](https://en.wikipedia.org/wiki/DNS_security_extensions)
- [Network Segmentation & VLANs](https://en.wikipedia.org/wiki/Virtual_LAN)

---

**NEON-SHIELD: Demonstrating why network security matters.** 🔐

For questions or security concerns, open an issue on GitHub.
