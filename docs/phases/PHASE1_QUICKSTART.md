# 🚀 MITM-INTERCEPT Phase 1: Quick Start Guide

**Close-Range WiFi Attack Demonstrations**

> **BEFORE YOU START:** Read the full legal disclaimer in README.md. This tool demonstrates FEDERAL CRIMES. Only use on networks/devices you own or are explicitly authorized to test.

---

## ⚠️ CRITICAL: Authorization Confirmation

You will be asked to confirm authorization **multiple times**. This is intentional.

- You must type `YES` or `yes` to confirm
- Large red warning banners will appear before each attack
- If you feel uncomfortable, **DO NOT PROCEED**

---

## 🎯 Phase 1 Attacks (Out-of-the-Box)

### Attack 1: Rogue Access Point (Evil Twin)

**What it does:** Creates a fake WiFi network. Nearby devices auto-connect, exposing all traffic to MITM-INTERCEPT.

**Startup command (one line):**
```bash
sudo python3 main_cli.py phase1 ap-mode --ssid "Starbucks_WiFi" -y
```

**What happens:**
1. MITM-INTERCEPT broadcasts fake "Starbucks_WiFi" network
2. Nearby devices that previously connected to Starbucks auto-join
3. All their traffic now flows through MITM-INTERCEPT
4. You can see passwords, emails, messages in real-time
5. Press Ctrl+C to stop

**Why it's powerful:**
- No per-device configuration needed
- Devices auto-connect (learned behavior)
- ALL traffic intercepted (not just network-level, but full end-to-end)
- Users don't realize they're on fake network

**Educational message:**
> "This is why you shouldn't auto-connect to WiFi networks. Your phone remembers networks and will connect to lookalike ones. An attacker can create a fake network with the same name and steal all your data."

---

### Attack 2: Network Enumeration & Vulnerability Scan

**What it does:** Scans nearby WiFi networks and shows which ones are vulnerable to attacks.

**Startup command (one line):**
```bash
sudo python3 main_cli.py phase1 scan-networks
```

**What happens:**
1. Discovers all WiFi networks in range
2. Shows encryption type, signal strength, channel
3. Marks vulnerable networks (WEP, open, weak encryption)
4. Shows privacy risks (SSID broadcasting reveals location patterns)

**Output example:**
```
Found 12 networks:

🔴 Free_Starbucks (WEP) | Signal: -40dBm | VULNERABLE: WEP (broken)
🟡 Guest_WiFi (WPA) | Signal: -55dBm | WEAK: WPA (outdated)
🟢 Starbucks_Employee (WPA2) | Signal: -45dBm | Acceptable: WPA2
```

**Why it matters:**
- Attackers scan networks exactly like this to find vulnerable ones
- You have no idea what networks are near you
- Many use broken or weak encryption
- Your network name can reveal personal information

**Educational message:**
> "Right now, there are dozens of WiFi networks around you. Some are vulnerable. An attacker can see all of them and knows exactly which ones to target."

---

### Attack 3: WiFi Deauthentication

**What it does:** Forces a device to disconnect from WiFi. When combined with Rogue AP, forces reconnection to our fake network.

**Startup command (one line):**
```bash
sudo python3 main_cli.py phase1 deauth \
  --target-mac "AA:BB:CC:DD:EE:FF" \
  --gateway-mac "11:22:33:44:55:66" \
  --ssid "Starbucks_WiFi" -y
```

**To find target MAC and gateway MAC:**
```bash
# On the target device (Linux):
ip link show  # Your device's MAC address

# On your machine, scan the network:
sudo python3 main_cli.py phase1 scan-networks  # Shows networks
arp -a  # Shows devices and their MACs
```

**What happens:**
1. Sends forged WiFi "disconnect" frames
2. Device loses WiFi connection
3. Device automatically searches for networks
4. If your Rogue AP is nearby, device auto-connects to it
5. Now all traffic is intercepted

**Why it's powerful:**
- Works from 100+ meters away (WiFi range)
- No need to be on target network
- Forces device to our fake AP
- Cascades into full MITM

**Educational message:**
> "WiFi connections can be forcibly disconnected by anyone in range. When you reconnect, you might join an attacker's fake network instead. This is why WPA3 has built-in deauth protection."

---

## 📋 Full Feature Reference

### Command: `ap-mode` (Rogue Access Point)

```bash
sudo python3 main_cli.py phase1 ap-mode \
  --interface wlan0 \          # WiFi interface (default: wlan0)
  --ssid "Starbucks_WiFi" \    # Network name to broadcast
  --channel 6 \               # WiFi channel (1-11, default: 6)
  -y                          # Skip confirmation
```

**Options:**
- `--interface`: WiFi interface (find with `iwconfig` or `ip link show`)
- `--ssid`: Network name to broadcast (use real network names like "Starbucks_WiFi", "Airport_Free", "Hotel_Guest")
- `--channel`: WiFi channel (1-11 for 2.4GHz, try 6 or 11 for less interference)
- `-y`: Skip confirmation (but you'll see the disclaimer anyway)

**Requirements:**
- Root privileges (sudo)
- `hostapd` and `dnsmasq` installed
- WiFi interface capable of AP mode

**Install requirements:**
```bash
sudo apt-get install hostapd dnsmasq
```

---

### Command: `scan-networks` (Network Enumeration)

```bash
sudo python3 main_cli.py phase1 scan-networks \
  --interface wlan0           # WiFi interface (default: wlan0)
```

**Requirements:**
- Root privileges (sudo)
- `iw` command installed

**Install requirements:**
```bash
sudo apt-get install iw
```

---

### Command: `deauth` (Deauthentication Attack)

```bash
sudo python3 main_cli.py phase1 deauth \
  --interface wlan0 \                    # WiFi interface
  --target-mac "AA:BB:CC:DD:EE:FF" \     # Device to disconnect
  --gateway-mac "11:22:33:44:55:66" \    # Router MAC
  --ssid "Network Name" \                # Network name (for logging)
  --count 10 \                           # Number of deauth frames
  -y                                     # Skip confirmation
```

**Requirements:**
- Root privileges (sudo)
- `airmon-ng` and `aireplay-ng` (from aircrack-ng suite)

**Install requirements:**
```bash
sudo apt-get install aircrack-ng
```

---

## 🎬 Demo Walkthrough (Home Lab)

### Setup: Two WiFi-enabled devices
- Device A: Attacker machine (Linux laptop with MITM-INTERCEPT)
- Device B: Target device (iPhone, Android, or another laptop)

### Demo Steps:

**Step 1: Create Rogue AP**
```bash
# On Device A:
sudo python3 main_cli.py phase1 ap-mode --ssid "Starbucks_WiFi" -y

# Output shows:
# ✅ ROGUE ACCESS POINT ACTIVE
# 📡 Broadcasting: Starbucks_WiFi
# 📍 AP IP: 192.168.100.1
# 🔌 Clients will connect to: 192.168.100.1
```

**Step 2: Device B Auto-Connects**
- On Device B, go to WiFi settings
- It will show "Starbucks_WiFi" (our fake AP)
- Since it previously connected to Starbucks WiFi, it might auto-connect
- OR manually select and connect to our fake AP

**Step 3: Watch Traffic (In another terminal)**
```bash
# Open the control panel to see live traffic:
firefox http://127.0.0.1:7070/

# You'll see:
# - Every website Device B visits
# - Every password it enters
# - Every message it sends
# - All email, all personal data
```

**Step 4: Stop Attack**
```bash
# In the ap-mode terminal:
# Press Ctrl+C
# ✅ Rogue AP stopped
```

**Step 5: Debrief**
Explain to Device B user:
> "Your phone auto-connected to a fake network I created. I could see every website you visited, every password you entered, every message you sent. This is why:
> - You should never auto-connect to WiFi
> - You should use a VPN on all public WiFi
> - You should enable 2FA on important accounts
> - You should never reuse passwords"

---

## ⚠️ Legal Reminders

**This is a federal crime without authorization:**

| Attack | Law | Penalty |
|--------|-----|---------|
| Rogue AP | Computer Fraud & Abuse Act, Wiretap Act | Up to 10 years, $250k+ |
| Deauth | FCC regulations, CFAA | Up to 10 years, $250k+ |
| Traffic Interception | Electronic Communications Privacy Act | Up to 15 years, $250k+ |

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

1. **WiFi is not secure by default** — Anyone in range can intercept traffic
2. **Auto-connect is dangerous** — Devices connect to lookalike networks
3. **HTTPS is critical** — But even HTTPS can be intercepted if you trust attacker's cert
4. **VPNs work** — They encrypt traffic so attacker can't see content even if you connect to fake network
5. **2FA is essential** — Even if password is stolen, 2FA blocks account takeover
6. **Network security requires layers** — No single defense is enough; need WPA3 + hidden SSID + strong password + VPN

---

## 🚨 Troubleshooting

### "hostapd not found"
```bash
sudo apt-get install hostapd
```

### "aireplay-ng not found"
```bash
sudo apt-get install aircrack-ng
```

### "Monitor mode failed"
```bash
# Some interfaces don't support monitor mode
# Check with:
sudo iwconfig

# Look for "Monitor" in the "Modes" line
```

### "Deauthentication didn't work"
- Make sure you have the correct MACs (use `arp -a` and `iwconfig`)
- Try increasing `--count` (e.g., `--count 20`)
- Make sure interface is in monitor mode
- Try a different WiFi channel

### "Device won't connect to rogue AP"
- Use a popular network name (Starbucks_WiFi, Airport_Free, Hotel_Guest)
- Make sure you're on same WiFi channel
- Make sure DHCP server is running (dnsmasq)

---

That's it! You now have a powerful demonstration of why WiFi security matters.

**Remember:** This tool is for education and authorized testing only. Use responsibly. 🔐
