# ⚡ PROJECT: MITM-INTERCEPT // MITM PROXY LAB

```
   _  _ ___ ___  _  _    ___ _  _ ___ ___ _    ___
   |\ | |__ |  \ |\ | __  |  |__| |__ |__ |    |  \
   | \| |___|__/ | \|     |  |  | |___|___|___ |__/
   
      [!] INTERCEPT // INSPECT // TRANSFORM 
```

MITM-INTERCEPT is a modular, high-performance HTTP/HTTPS Man-in-the-Middle (MitM) inspection proxy designed for security research, analysis, and network debugging in isolated environments. By establishing an active decrypting gateway, it intercepts downstream client requests, parses header metadata, and executes on-the-fly content transformation (specifically replacing web images with a custom asset).

---

## 🛑 DISCLAIMER — READ BEFORE USE

**THIS PROJECT IS FOR EDUCATIONAL AND AUTHORIZED SECURITY-RESEARCH PURPOSES ONLY.**

MITM-INTERCEPT performs an active Man-in-the-Middle attack: it decrypts and modifies other devices' traffic. That is only legal and ethical when you have clear authorization to do it. By using this tool you agree that:

* You will **only** run it against networks and devices that you personally own, **or** for which you hold explicit written authorization (e.g. a signed pentest engagement, a CTF you're competing in, or a classroom lab you control).
* You will **never** run it — especially the `--auto` zero-config network mode — against shared, public, employer, school, or any other network where other people's devices you don't own or have consent for might be present (coffee shops, offices, dorms, airports, etc.). ARP spoofing devices you don't have authorization for is a form of unauthorized network interception/wiretapping and is illegal in most jurisdictions, regardless of intent or how "harmless" the payload (e.g. swapping an image) seems.
* You understand `--auto` mode actively attacks ARP resolution on the LAN and can disrupt connectivity for every device it targets; only use it in a controlled lab.
* You are responsible for securing generated CA private keys (`certs/`) and for un-trusting/removing the MITM-INTERCEPT Root CA and restoring normal proxy/network settings on any device when you're done testing.

The author accepts no liability for misuse or damage caused by this utility. If you are not sure you're authorized to run this against a given network or device, **do not run it.**

---

## 🌌 SYSTEM CAPABILITIES

*   **HTTP Request Parsing:** Low-overhead raw socket parser that extracts headers, connection states, and target URIs.
*   **Dynamic MitM Certificate Issuance:** On-the-fly Generation of domain certificates signed by a custom local Root CA (complete with Subject Alternative Name (SAN) structures required by modern web browsers).
*   **Decrypted SSL/TLS Inspection:** Intercepts secure `CONNECT` requests, establishing dual-sided secure sockets to inspect encrypted traffic streams.
*   **Active Payload Substitution:** Dynamic byte pattern matching for images (based on HTTP `Content-Type` headers and resource extensions) to swap network assets with a localized payload (`rax_logo.png`).
*   **Cache Prevention Overrides:** Automatically rewrites caching headers (`Cache-Control`, `Pragma`, `Expires`) on transformed payloads to bypass client-side caching.
*   **Zero-Config Auto Network Mode (`--auto`):** ARP-spoofs devices on the local subnet and transparently NAT-redirects their HTTP/HTTPS traffic into the proxy — no manual per-device proxy configuration required. See [Auto Network Mode](#-auto-network-mode-zero-config-interception) below. Requires Linux + root, and explicit on-screen authorization confirmation before it will run.

---

## 🛠️ ARCHITECTURE

The tool is divided into clean, modular blocks:

*   📂 **`ca.py`**: The Dynamic CA Engine. Generates 2048-bit RSA keys and Root CA certificates. Reuses a pre-generated domain private key to accelerate handshake generation (~50x speed increase over signing with fresh keys).
*   📂 **`proxy.py`**: The multi-threaded interception socket engine. Maps connection lifecycles, initiates upstream tunnels, routes traffic, and injects payload modifications. Also hosts the `--auto` mode orchestrator and the transparent HTTP/HTTPS listeners it uses.
*   📂 **`netdiscover.py`**: Auto-mode network discovery — detects the active interface/gateway/subnet and ARP-scans the LAN for live hosts.
*   📂 **`arpspoof.py`**: Auto-mode ARP poisoning engine — places this host in the traffic path between target device(s) and the gateway, and cleanly restores real ARP mappings on shutdown.
*   📂 **`iptables_ctl.py`**: Auto-mode transparent redirect controller — enables IP forwarding and installs/removes the iptables NAT rules that funnel real port 80/443 traffic into the proxy's transparent listeners.
*   📂 **`local_images/rax_logo.png`**: The binary payload injected into intercepted image packets.
*   📂 **`.gitignore`**: Safety config to guarantee that private CA keys, dynamic certs, and test materials never leave the local environment.

---

## 💻 QUICKSTART & COMMAND LINE VALIDATION

### 1. Boot up the Intercept Engine
Fire up the proxy daemon inside your laboratory network:
```bash
python3 proxy.py
```
The engine binds to port `8080` on all local interfaces (`0.0.0.0`), meaning it's reachable from both your local machine and other devices on the same Wi-Fi/local network.

### 2. Connect Local Devices (Wi-Fi Interception)
To intercept and configure a device on your local Wi-Fi:
1. Ensure your test device (e.g., iPhone, Android phone, or another laptop) is connected to the **same Wi-Fi network**.
2. Open a browser on the device and navigate to:
   ```
   http://<proxy-host-ip>:8080
   ```
   *(The terminal console will print your host's local IP address when starting up.)*
3. You will see the **MITM-INTERCEPT Dashboard**.
4. Tap **Download Root CA Certificate** to save `ca.crt` to your device.
5. Follow the step-by-step instructions on the dashboard corresponding to your device (iOS, Android, or desktop OS) to install and trust the Root CA certificate.
6. Configure the device's Wi-Fi network settings to use a **Manual Proxy**:
   - **Server/Host IP**: `<proxy-host-ip>`
   - **Port**: `8080`

### 3. Quickstart Validation (Localhost CLI)
If testing locally on the proxy host machine:

#### Linux System CA Trust Setup:
```bash
sudo cp certs/ca.crt /usr/local/share/ca-certificates/mitm-intercept-ca.crt
sudo update-ca-certificates
```

#### Set Terminal Proxy Environment:
```bash
export http_proxy=http://127.0.0.1:8080
export https_proxy=http://127.0.0.1:8080
```

#### Run Curl Validation:
```bash
# HTTP test request
curl -v -x http://127.0.0.1:8080 http://example.com/some-asset.png -o test_http.png

# HTTPS test request
curl -v -x http://127.0.0.1:8080 --cacert certs/ca.crt https://example.com/some-secure-asset.png -o test_https.png
```
*Observe that the retrieved images are substituted with the RAX logo payload, and metrics will update live on the dashboard.*

---

## 🌐 AUTO NETWORK MODE (ZERO-CONFIG INTERCEPTION)

> ⚠️ **Read the [Disclaimer](#-disclaimer--read-before-use) above first.** This mode actively attacks ARP resolution for every device on the LAN. Only run it on a network and against devices you own or are explicitly authorized to test.

The default mode above requires you to manually set a proxy and install the CA on each test device. `--auto` mode removes that step for devices already on your LAN by combining:

1. **Network discovery** — ARP-scans your subnet to find live hosts.
2. **ARP spoofing** — poisons ARP caches so target devices' traffic routes through this host.
3. **Transparent NAT redirect** — `iptables` rules silently forward real port 80/443 traffic into the proxy's transparent listeners (no client-side proxy setting needed).

**Important limitation:** ARP spoofing + transparent redirect gets a device's *traffic* flowing through the proxy automatically, but it does **not** bypass certificate validation. Plaintext HTTP images will be substituted immediately. HTTPS sites will still show the browser's untrusted-certificate warning on any device that hasn't separately downloaded and trusted the MITM-INTERCEPT Root CA (see step 4 of the manual Quickstart, or the dashboard's CA guides) — this tool does not silently defeat TLS.

### Requirements
* Linux host with `iptables` and root privileges (`sudo`).
* `pip install -r requirements.txt` (adds `scapy` for ARP spoofing/discovery).

### Usage

```bash
# Discover every other live host on the subnet and intercept all of them:
sudo python3 proxy.py --auto

# Or restrict to specific devices you've confirmed authorization for:
sudo python3 proxy.py --auto --targets 192.168.1.23,192.168.1.45

# Non-interactive (e.g. scripted lab setup) — still only use where authorized:
sudo python3 proxy.py --auto -y
```

On startup, `--auto` mode prints an authorization banner and requires you to type `YES` to confirm you own (or are authorized to test) the network and every targeted device, unless `-y`/`--yes` is passed. On exit (`Ctrl+C`), it automatically restores real ARP mappings and removes the iptables rules it added.

---

## ⚡ SECURITY ANALYSIS: HOW DEFENDERS PREVENT MITM

Understanding how interception works highlights the importance of modern network defenses. To block unauthorized TLS decryption, production environments deploy:
1.  **Certificate Pinning (HPKP / Custom Implementations):** Mobile applications and web browsers can be hardcoded to trust only specific certificate hashes. Even if a device trusts the proxy CA, the application rejects the handshake because the generated certificate hash does not match the pinned hash.
2.  **Strict Transport Security (HSTS):** Enforces HTTPS connections and prevents browsers from ignoring cert verification warnings.
3.  **Encrypted Client Hello (ECH):** Modern TLS extensions designed to hide the SNI (Server Name Indication), making it harder for simple firewalls to identify the target domain before the handshake.
4.  **Dynamic ARP Inspection (DAI) / Port Security:** Managed switches can validate ARP replies against known IP-MAC bindings (often learned from DHCP snooping) and drop forged ones, neutralizing the ARP spoofing technique `--auto` mode relies on.
5.  **802.1X / WPA2/3-Enterprise with Client Isolation:** Prevents devices on the same Wi-Fi network from ARP-poisoning each other in the first place by isolating clients at layer 2.
