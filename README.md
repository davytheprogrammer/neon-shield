> [!IMPORTANT]
> ### 📡 SYSTEM STATUS: ACTIVE DEVELOPMENT & MAINTENANCE
> * **REPOSITORY BRANCH:** `main` (active refactoring and feature integrations)
> * **STABILITY INDEX:** Bleeding-edge. APIs, configuration schemas, and modules are subject to frequent updates.
> * **ENGAGEMENT POLICY:** Technical contributions, issue reports, and defensive suggestions are highly welcomed.
> * **SUPPORT THE PROJECT:** If this research suite empowers your work, please consider dropping a **⭐ Star**, **🍴 Forking** the codebase, or **👀 Watching** to track updates.

# ⚡ NEON-SHIELD v2.0 — Advanced MITM Lab

> [!WARNING]
> **RESTRICTED RESEARCH TOOL.** Authorized security audits, penetration testing demonstrations, and defensive security training only. Unauthorized layer-2 manipulation, packet interception, and TLS tampering are major offenses under international computer misuse regulations.

```
   _  _ ___ ___  _  _    ___ _  _ ___ ___ _    ___
   |\ | |__ |  \ |\ | __  |  |__| |__ |__ |    |  \
   | \| |___|__/ | \|     |  |  | |___|___|___ |__/
   
      [!] INTERCEPT // INSPECT // TRANSFORM 
```

### The Cyber-Security Research & Demonstration Environment

**NEON-SHIELD** is a production-grade, highly-extensible Man-in-the-Middle (MITM) network auditing and research platform. Architected for defensive security analysis, live vulnerability demonstration, and cybersecurity instruction, NEON-SHIELD exposes the mechanics of local network manipulation and security protocol bypasses.

By executing real-world traffic interception and payload transformations, the platform provides security teams and researchers with the exact insights needed to deploy, test, and validate robust enterprise defenses—including HTTPS enforcement, strict certificate pinning, secure authentication mechanisms, and network micro-segmentation.

---

## 🔴 [0x00] Legal Disclaimer & Terms of Engagement

> [!CAUTION]
> **UNAUTHORIZED INTERCEPTION IS A FELONY.**
> Executing MITM interceptors on networks or devices without prior, written, explicit authorization from the respective asset owners is a severe breach of computer misuse acts worldwide.

NEON-SHIELD integrates active threat simulation mechanics:
* **Layer-2 Redirection:** ARP cache poisoning to route target client traffic through the host.
* **TLS Termination & Decryption:** Certificate spoofing to inspect encrypted HTTP/S application streams.
* **Automatic Credential Extraction:** Regular expression scanners that pull passwords and tokens from login payloads.
* **DNS Hijacking:** Scoped DNS response forging to redirect domain name requests.
* **Inline Payload Injector:** Runtime content replacement rules for HTML, JS, and image assets.
* **Full-Stream Auditing:** Logging HTTP request-response flows to local disk.

### Target Validation Agreement
By compiling, deploying, or launching NEON-SHIELD, you explicitly assert that:
1. You possess signed, written permission authorizing network audits on all targeted hosts.
2. The platform is operated solely within a designated, isolated laboratory or testing environment (e.g., dedicated VLANs, corporate ranges, or home labs).
3. You assume all legal and operational liability for packets intercepted or altered by this software.
4. The platform will not be used to harvest credentials, spy, or perform malicious actions on unauthorized users.

**If you are unsure whether you possess authorization to operate this tool, DO NOT INITIALIZE IT.**

---

## 🌟 [0x01] Core Tactical Capabilities

### ⚡ Rapid Deployment & Host Discovery
* **Zero-Config Auto Mode:** Initialize target routing with a single command (`sudo python3 main_cli.py start`) to automatically discover active LAN hosts.
* **Transparent Packet Capture:** Capture and relay packets dynamically without modifying target client network profiles.
* **Interactive Setup Wizard:** Built-in interactive setup utility helps you configure interfaces, gateways, and modules dynamically.

### 🔍 Deep Stream Interception & Payload Mutation
* **Stream Auditor:** Monitor HTTP/HTTPS request/response lifecycles, logging methods, destination domains, status codes, and source IPs.
* **Credential Harvest Module:** Automate extraction of plaintext credentials from HTTP Basic authentication headers and form payloads.
* **Scoped DNS Spoofing:** Restrict DNS redirection rules to target domains to minimize operational noise.
* **Dynamic HTML/JS Injector:** Modify raw HTML responses, inject custom script banners, or hot-swap network images on the fly.

### ⚙️ Operational Stability & Reliability
* **YAML Infrastructure File:** Centralize routes, modules, and target options within a unified configuration file (`neon-shield.yml`).
* **Active Watchdog Monitor:** Background health thread monitors ARP tables and firewall rules, executing automatic repairs upon failure.
* **Crash-Resilient State Engine:** Log operational states to disk to support automatic restart and cleanup validation.
* **Dry-Run Mode:** Execute config validations, network interface checks, and routing table reviews without firing active spoofs.
* **Emergency Tear-down:** Restore routing tables and clear iptables chains instantly with the built-in `cleanup.sh` helper.
* **Systemd Integration:** Package and run the platform daemon as a persistent system service.

### 💻 Unified Command-Line Interface
NEON-SHIELD exposes a clean CLI syntax to manage local interceptors:
```bash
neon-shield init      # Run the interactive configuration wizard
neon-shield start     # Load settings and activate local redirection
neon-shield stop      # Cease active interception and restore target tables
neon-shield status    # Audit running modules and component health
neon-shield cleanup   # Execute manual recovery and flush system tables
neon-shield test      # Validate config limits and permissions (dry-run)
```

### 📊 Administrative Monitoring Panels
* **Public Client Hub:** Hosted at `http://<proxy-ip>:8080` – enables target hosts to retrieve CA certificates and view trusted status checklists.
* **Local Control Dashboard:** Hosted at `http://127.0.0.1:7070` (Localhost only) – visualizes intercepted packet streams and captured credentials in real-time.

---

## 🛡️ [0x02] Threat Matrix & Defensive Alignment

NEON-SHIELD is built to validate modern network defenses by demonstrating the exact mechanisms utilized to bypass them:

| Threat Vector | Interception Demonstration | Enterprise-Grade Countermeasure |
| :--- | :--- | :--- |
| **ARP Spoofing / Poisoning** | Redirects Layer-2 packets by poisoning target ARP tables. | **Dynamic ARP Inspection (DAI)**, static MAC bindings, 802.1X Network Access Control. |
| **Transparent Redirection** | Intercepts packets at the local router layer using iptables forwarding. | **Network Segmentation**, strict VLAN isolation, end-to-end IPsec / VPN tunnels. |
| **TLS/SSL Interception** | Decrypts HTTPS streams using a trusted local Root Certificate Authority. | **HTTP Strict Transport Security (HSTS)**, Certificate Pinning, Certificate Transparency (CT). |
| **Credential Harvesting** | Extracts passwords from HTTP requests and forms. | **HTTPS-only configuration**, secure session cookies, OAuth 2.0 / OIDC, Multi-Factor Authentication (MFA). |
| **DNS Spoofing / Hijacking** | Forges DNS responses to redirect traffic to local platforms. | **DNSSEC validation**, DNS-over-HTTPS (DoH), DNS-over-TLS (DoT). |
| **Active Content Injection** | Modifies HTTP response bodies to execute scripts or replace assets. | **Content Security Policy (CSP)**, Subresource Integrity (SRI), end-to-end cryptographic transit. |

---

## 🚀 [0x03] Deployment & Rapid Initialization

### 1. Clone & Install Dependencies
Verify Python 3.8+ and `pip` are configured on your host system:
```bash
git clone https://github.com/YOUR_USERNAME/neon-shield.git
cd neon-shield
pip install -r requirements.txt
chmod +x cleanup.sh
```

### 2. Configure Operational Variables
Execute the setup assistant to verify host configurations and interface settings:
```bash
sudo python3 main_cli.py init
```
The assistant prompts for:
* Affirmation of authorized usage terms.
* Network interface selection.
* Specifying target hosts and gateway endpoints.
* Activating content injection rules and DNS overrides.
* Configuring log rotation files.

Parameters are stored in [neon-shield.yml](neon-shield.yml).

### 3. Initiate Active Mode
Run the interceptor core:
```bash
sudo python3 main_cli.py start
```

* **CA Certificate Provisioning:** Have target clients access `http://<your-ip>:8080/ca.crt` to download the root CA.
* **Administrative Monitor:** Point your browser to `http://127.0.0.1:7070` to view captured traffic logs.
* **Graceful Termination:** Send `Ctrl+C` to stop; the runtime automatically flushes routing rules and restores targets.

### operational Recipes
```bash
# Target specific hosts directly, bypassing interactive prompts
sudo python3 main_cli.py start --targets 192.168.1.50,192.168.1.51 -y

# Enable scoped DNS redirection for specific hostnames
sudo python3 main_cli.py start --dns-redirect "example.com:192.168.1.1" -y

# Verify configuration schemas without starting network spoofing
python3 main_cli.py test

# Emergency manual restoration of host iptables and ARP tables
sudo ./cleanup.sh
```

---

## 📖 [0x04] Intelligence Directory

Refer to these files for detailed setup options and structural references:
* **[SETUP.md](SETUP.md):** Manual deployment options, routing setups, CLI arguments, and recovery steps.
* **[neon-shield.yml](neon-shield.yml):** Reference configuration file containing descriptions for all modular attributes.
* **System Help:** Run `python3 main_cli.py --help` to list all command line arguments.

---

## 🏗️ [0x05] Architecture & Subsystem Layout

The NEON-SHIELD core is divided into discrete, specialized modules:

* **[main_cli.py](main_cli.py):** Main entry point; a Click-based Command Line Interface.
* **[proxy.py](proxy.py):** Core MITM proxy engine handling HTTP, HTTPS, and DNS socket listeners.
* **[config.py](config.py):** Schema validation module parsing and enforcing configuration boundaries.
* **[netdiscover.py](netdiscover.py):** ARP scanning utility mapping active subnets.
* **[arpspoof.py](arpspoof.py):** Attack script poisoning ARP tables to redirect client traffic.
* **[iptables_ctl.py](iptables_ctl.py):** Low-level iptables manager configuring system NAT rules.
* **[content_rules.py](content_rules.py):** Stream modifier wrapper matching and replacing target request-response content.
* **[creds_capture.py](creds_capture.py):** Scans payloads to locate credentials and cookies.
* **[traffic_log.py](traffic_log.py):** Collector interface processing traffic logs securely in memory.
* **[dns_spoof.py](dns_spoof.py):** Local DNS server returning forged IP entries for allow-listed domains.
* **[health_monitor.py](health_monitor.py):** Watchdog thread verifying route structures and proxy availability.
* **[state_manager.py](state_manager.py):** State manager verifying cleanup on restarts.
* **[log_handler.py](log_handler.py):** Structured log writer outputting rotational data.

---

## 🧪 [0x06] Penetration Testing & Audit Workflows

For authorized penetration testing assessments, utilize this standard execution workflow:

```bash
# Step 1: Run the configuration helper
sudo python3 main_cli.py init

# Step 2: Validate routing rules and configuration bounds
python3 main_cli.py test

# Step 3: Enable active redirection
sudo python3 main_cli.py start -y

# Step 4: Monitor traffic feeds in real time
open http://127.0.0.1:7070/

# Step 5: Extract session logs for reports
cat logs/traffic.jsonl
cat logs/credentials.jsonl

# Step 6: Gracefully restore host network configurations
sudo python3 main_cli.py stop
# (Emergency cleanup fallback)
sudo ./cleanup.sh
```

All logging outputs are structured in JSON Lines format (`.jsonl`), ready to be loaded into analysis engines or visualization platforms.

---

## 🎛️ [0x07] Operational Safeguards & Controls

To minimize lab disruption, NEON-SHIELD embeds several protective constraints:
* **Privileged Escalation Guard:** ARP spoofing and routing rules fail safely if initialized without root/sudo clearance.
* **Authorization Auditing:** The CLI forces a legal agreement confirmation before activation, which is written to persistent audit logs.
* **Watchdog Watch:** The background thread checks routing entries every 5 seconds. If rules are altered or cleared, it attempts a recovery sequence.
* **Local Data Enclave:** Traffic logs and extracted auth details are stored locally. The platform does not send data to external servers.
* **Signal Capture Rollback:** Signals like `SIGINT` and `SIGTERM` are caught to trigger immediate network restorations.

---

## 📊 [0x08] Testing & QA Pipeline

NEON-SHIELD utilizes a dedicated test suite to verify code stability:

```bash
# Run all tests using pytest
pytest tests/ -v

# Run the test suite and output an HTML coverage report
pytest tests/ --cov=. --cov-report=html
```

> [!NOTE]
> Testing is fully integrated with GitHub Actions CI, validating quality guidelines, schema types, and module actions on every commit.

---

## ⚙️ [0x09] Configuration Specification

Options are declared inside `neon-shield.yml` and organized as follows:
* **`network`:** Active interface binding, target gateway address, and discovery IP subnets.
* **`content_rules`:** Target files and directories for injecting script codes or replacing image resources.
* **`dns_spoof`:** Scoped DNS domain-to-IP configurations.
* **`logging`:** Rotation maximums, log locations, and level thresholds (`DEBUG`, `INFO`).
* **`health_monitor`:** Interval timings and error tolerances.
* **`web_interfaces`:** Bind options and host ports for public and private dashboards.

---

## 🖥️ [0x0A] Desktop Control Hub: Building Tauri v2

NEON-SHIELD packages a modern desktop interface developed with React and Tauri v2.

### 1. Compile System Libraries (Linux / Ubuntu / Debian / Pop!_OS)
Install dependencies and configure the Rust compiler toolchain:

```bash
# Configure system libraries and compilation tools
sudo apt update
sudo apt install -y libwebkit2gtk-4.1-dev build-essential curl wget file libxdo-dev libssl-dev libayatana-appindicator3-dev librsvg2-dev

# Configure the Rust compiler
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
```

### 2. Build the Desktop Client
Navigate to the GUI module, install packages, and start compilation:

```bash
cd gui
npm install

# Run in desktop hot-reload development mode
npm run tauri dev

# Package the release binary
npm run tauri build
```

Compiled application binaries (AppImage, deb) are built within `gui/src-tauri/target/release/bundle/`.

---

## 🛠️ [0x0B] Troubleshooting & Port Recovery

If the platform is terminated abruptly, bind errors such as `OSError: [Errno 98] Address already in use` may prevent restarts. 

Use these terminal commands to clear blocking sockets:

### Method A: Targeted Port Clearing (fuser)
Instantly kill tasks binding designated TCP ports:
```bash
# Free the WebSocket Daemon socket (8766)
sudo fuser -k 8766/tcp

# Free the Client Dashboard port (8080)
sudo fuser -k 8080/tcp

# Free the Local Control Panel port (7070)
sudo fuser -k 7070/tcp
```

### Method B: Manual PID Resolution (lsof)
Locate the PID binding the socket:
```bash
# Audit port 8766
sudo lsof -i :8766

# Kill target process
sudo kill -9 <PID>
```

### Method C: Emergency Recovery Script
Run the script to clear iptables rules and restore network states:
```bash
sudo ./cleanup.sh
```

---

## 🤝 [0x0C] Contributing & Collaboration

We welcome developer involvement. When proposing pull requests:
1. **Terms Check:** Verify compliance with the target engagement rules.
2. **Add Tests:** Write unit tests for new modules.
3. **Document Updates:** Verify inline annotations and configuration templates are current.

---

## 📄 [0x0D] License & Terms

NEON-SHIELD is licensed under the **MIT License**. For complete terms, see the `LICENSE` file.

> [!WARNING]
> **Warranty Disclaimer:** The software is provided "as is" without warranty of any kind. Users assume all operational risks. The authors assume no liability for unauthorized, illegal, or unethical utilization of this platform.

---

## 🎓 [0x0E] Educational Resources

* **[OWASP: Man-in-the-Middle (MITM) Attacks](https://owasp.org/www-community/attacks/Manipulator-in-the-middle_attack):** Detailed breakdown of MITM concepts and countermeasures.
* **[Why HTTPS Matters](https://https.cio.gov/):** Public guidelines detailing TLS enforcement advantages.
* **[OWASP: Certificate Pinning Guide](https://owasp.org/www-community/controls/Pinning):** Implementation and analysis of certificate validation defenses.
* **[Introduction to DNSSEC](https://en.wikipedia.org/wiki/DNS_security_extensions):** DNS security extensions and validation mechanics.
* **[Network Segmentation & VLANs](https://en.wikipedia.org/wiki/Virtual_LAN):** VLAN principles and broadcast domain containment.

---

**NEON-SHIELD: Demonstrating why network security matters.** 🔐

For questions or security concerns, open an issue on GitHub.

