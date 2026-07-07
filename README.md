# ⚡ PROJECT: NEON-SHIELD // MITM PROXY LAB

```
   _  _ ___ ___  _  _    ___ _  _ ___ ___ _    ___
   |\ | |__ |  \ |\ | __  |  |__| |__ |__ |    |  \
   | \| |___|__/ | \|     |  |  | |___|___|___ |__/
   
      [!] INTERCEPT // INSPECT // TRANSFORM 
```

NEON-SHIELD is a modular, high-performance HTTP/HTTPS Man-in-the-Middle (MitM) inspection proxy designed for security research, analysis, and network debugging in isolated environments. By establishing an active decrypting gateway, it intercepts downstream client requests, parses header metadata, and executes on-the-fly content transformation (specifically replacing web images with a custom asset).

---

## 🛑 DISCLAIMER

**WARNING:** This tool is designed strictly for educational, security auditing, and laboratory research purposes. It must only be deployed on systems and networks where you have explicit authorization and control. The author accepts no liability for misuse or damage caused by this utility. Always secure your certificate keys and disable proxy configurations when not active.

---

## 🌌 SYSTEM CAPABILITIES

*   **HTTP Request Parsing:** Low-overhead raw socket parser that extracts headers, connection states, and target URIs.
*   **Dynamic MitM Certificate Issuance:** On-the-fly Generation of domain certificates signed by a custom local Root CA (complete with Subject Alternative Name (SAN) structures required by modern web browsers).
*   **Decrypted SSL/TLS Inspection:** Intercepts secure `CONNECT` requests, establishing dual-sided secure sockets to inspect encrypted traffic streams.
*   **Active Payload Substitution:** Dynamic byte pattern matching for images (based on HTTP `Content-Type` headers and resource extensions) to swap network assets with a localized payload (`rax_logo.png`).
*   **Cache Prevention Overrides:** Automatically rewrites caching headers (`Cache-Control`, `Pragma`, `Expires`) on transformed payloads to bypass client-side caching.

---

## 🛠️ ARCHITECTURE

The tool is divided into clean, modular blocks:

*   📂 **`ca.py`**: The Dynamic CA Engine. Generates 2048-bit RSA keys and Root CA certificates. Reuses a pre-generated domain private key to accelerate handshake generation (~50x speed increase over signing with fresh keys).
*   📂 **`proxy.py`**: The multi-threaded interception socket engine. Maps connection lifecycles, initiates upstream tunnels, routes traffic, and injects payload modifications.
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
3. You will see the **NEON-SHIELD Dashboard**.
4. Tap **Download Root CA Certificate** to save `ca.crt` to your device.
5. Follow the step-by-step instructions on the dashboard corresponding to your device (iOS, Android, or desktop OS) to install and trust the Root CA certificate.
6. Configure the device's Wi-Fi network settings to use a **Manual Proxy**:
   - **Server/Host IP**: `<proxy-host-ip>`
   - **Port**: `8080`

### 3. Quickstart Validation (Localhost CLI)
If testing locally on the proxy host machine:

#### Linux System CA Trust Setup:
```bash
sudo cp certs/ca.crt /usr/local/share/ca-certificates/neon-shield-ca.crt
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

## ⚡ SECURITY ANALYSIS: HOW DEFENDERS PREVENT MITM

Understanding how interception works highlights the importance of modern network defenses. To block unauthorized TLS decryption, production environments deploy:
1.  **Certificate Pinning (HPKP / Custom Implementations):** Mobile applications and web browsers can be hardcoded to trust only specific certificate hashes. Even if a device trusts the proxy CA, the application rejects the handshake because the generated certificate hash does not match the pinned hash.
2.  **Strict Transport Security (HSTS):** Enforces HTTPS connections and prevents browsers from ignoring cert verification warnings.
3.  **Encrypted Client Hello (ECH):** Modern TLS extensions designed to hide the SNI (Server Name Indication), making it harder for simple firewalls to identify the target domain before the handshake.
