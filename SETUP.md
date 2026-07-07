# NEON-SHIELD Setup Guide

## ⚠️ DISCLAIMER — READ FIRST

**AUTHORIZED USE ONLY.** NEON-SHIELD performs federal-crime-level MITM attacks:
- ARP spoofing
- TLS decryption
- Credential capture
- DNS spoofing

These are **illegal without explicit authorization**. 

By continuing, you confirm:
✓ Every target device is owned by you OR you have written authorization  
✓ This network is yours OR you're authorized to test it  
✓ You understand the consequences: felony charges, fines, imprisonment  
✓ This is EDUCATION & AUTHORIZED RESEARCH ONLY  

**If unsure, DO NOT PROCEED.**

---

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/neon-shield.git
cd neon-shield

# Install dependencies
pip install -r requirements.txt

# Make cleanup script executable
chmod +x cleanup.sh

# (Optional) Install systemd service
sudo cp neon-shield.service /etc/systemd/system/
sudo systemctl daemon-reload
```

---

## Quick Start

### 1. First-Time Setup (Interactive Wizard)

```bash
sudo python3 main_cli.py init
```

This runs an interactive setup wizard that asks you to:
- Confirm authorization
- Configure network interface & target devices
- Choose content rules (image swap, HTML banner)
- Configure DNS spoofing (optional)
- Set logging preferences

Your answers are saved to `neon-shield.yml`.

### 2. Start Interception

```bash
sudo python3 main_cli.py start
```

This loads your config and starts intercepting traffic.

### 3. Access Dashboards

- **LAN Dashboard (CA Download):** http://your-ip:8080/
- **Control Panel (Live Traffic):** http://127.0.0.1:7070/ (localhost only)

### 4. Stop & Restore

```bash
# Graceful stop
sudo python3 main_cli.py stop

# Or press Ctrl+C during execution
```

Both restore your ARP tables and remove firewall rules.

---

## CLI Subcommands

| Command | Purpose |
|---------|---------|
| `init` | Interactive setup wizard |
| `start` | Start interception (loads config from neon-shield.yml) |
| `stop` | Stop & restore network |
| `status` | Check current status |
| `cleanup` | Emergency recovery (restore everything) |
| `test` | Validate config (dry-run, no spoofing) |

### Examples

```bash
# Start with specific targets
sudo python3 main_cli.py start --targets 192.168.1.50,192.168.1.51

# Dry-run to test configuration
python3 main_cli.py test

# Check status
python3 main_cli.py status

# Emergency cleanup
sudo cleanup.sh
```

---

## Configuration

Edit `neon-shield.yml` to customize:

```yaml
network:
  interface: eth0          # Leave blank to auto-detect
  targets: 192.168.1.0/24  # Comma-separated IPs or CIDR

content_rules:
  enable_image_swap: true
  enable_html_banner: true

dns_spoofing:
  enabled: false
  redirects:
    example.com: 192.168.1.1

logging:
  level: INFO              # DEBUG, INFO, WARN, ERROR
  file: logs/neon-shield.log
  enable_traffic_log: true
  enable_creds_log: true
```

---

## Troubleshooting

### "Permission denied"
NEON-SHIELD requires root for ARP spoofing & iptables. Run with `sudo`.

### "Device not being intercepted"
- Verify device is on the same LAN (not VPN, not different VLAN)
- Check ARP spoofing is active: `arp -a` on target device
- Verify iptables rules: `sudo iptables -t nat -L PREROUTING -n`

### "Certificate not trusted" on target
**This is normal and expected.** HTTPS security is working as designed. To see decrypted HTTPS traffic, the target device must manually download and trust the NEON-SHIELD Root CA from http://proxy-ip:8080/ca.crt

### Network doesn't recover after crash
Run the emergency cleanup script:
```bash
sudo ./cleanup.sh
```

---

## Advanced

### Systemd Service

Install NEON-SHIELD as a system service:

```bash
sudo cp neon-shield.service /etc/systemd/system/
sudo systemctl enable neon-shield
sudo systemctl start neon-shield
```

Monitor logs:
```bash
sudo journalctl -u neon-shield -f
```

### Custom Content Rules

Edit `content_rules.py` to add new transformations (e.g., replace videos, modify JSON).

### Health Monitoring

NEON-SHIELD runs background health checks (configurable in `neon-shield.yml`):
- Verifies ARP spoofing is still active
- Checks iptables rules are in place
- Auto-recovers if components fail

Enable debug logging to see health checks:
```bash
sudo python3 main_cli.py start --verbose
```

---

## For Penetration Testers

NEON-SHIELD is designed for authorized security research. Example workflow:

1. **Setup:** `sudo python3 main_cli.py init` (answer prompts for client network)
2. **Dry-run:** `python3 main_cli.py test` (validate before starting)
3. **Start:** `sudo python3 main_cli.py start -y` (skip confirmation if scripted)
4. **Monitor:** Open http://127.0.0.1:7070/ to watch live traffic & captured credentials
5. **Document:** Traffic log saved to `logs/traffic.jsonl` & `logs/credentials.jsonl`
6. **Cleanup:** `sudo python3 main_cli.py stop` or `sudo cleanup.sh`

---

## Safety & Ethics

- **This is a lab tool for authorized use only.** Do not use against anyone's network without permission.
- **Certificate warnings are a feature, not a bug.** They indicate HTTPS security is working.
- **Local-only storage.** All captured data stays on the machine running the proxy.
- **Audit logging.** Every authorization confirmation is logged.

---

See **README.md** for full feature documentation and legal disclaimers.
