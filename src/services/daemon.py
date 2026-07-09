#!/usr/bin/env python3
import asyncio
import json
import os
import secrets
import sys
import subprocess
import threading
import time
import yaml
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import websockets

# Constants
HOST = "127.0.0.1"
PORT = 8766
CONFIG_PATH = Path("mitm-intercept.yml")
LOGS_DIR = Path("logs_user")
TRAFFIC_LOG = LOGS_DIR / "traffic.jsonl"
CREDS_LOG = LOGS_DIR / "credentials.jsonl"
DAEMON_LOG = LOGS_DIR / "daemon.log"
DAEMON_AUTH_TOKEN = os.environ.get("NEON_SHIELD_DAEMON_TOKEN", "").strip()

# Ensure log directory exists
LOGS_DIR.mkdir(exist_ok=True)

# State variable to track the active running process
active_process = None
active_process_name = None  # e.g., "mitm", "ap", "deauth", "scan"
connected_clients = set()
process_lock = asyncio.Lock()

def log_daemon(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] [Daemon] {message}"
    print(formatted)
    try:
        with open(DAEMON_LOG, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception as e:
        print(f"Failed to write daemon log: {e}")

async def broadcast(message_dict):
    if not connected_clients:
        return
    message_str = json.dumps(message_dict)
    tasks = [asyncio.create_task(client.send(message_str)) for client in connected_clients]
    if tasks:
        await asyncio.wait(tasks)

async def heartbeat_loop():
    """Broadcasts a lightweight heartbeat every 5 seconds so the frontend
    can clearly distinguish 'connected but idle' from 'disconnected'."""
    while True:
        await asyncio.sleep(5)
        if connected_clients:
            await broadcast({
                "type": "heartbeat",
                "ts": time.time(),
                "running": active_process is not None,
                "process": active_process_name,
                "clients": len(connected_clients)
            })

async def tail_file(file_path, msg_type):
    """Tails a file asynchronously and broadcasts new lines as JSON to clients."""
    if not file_path.exists():
        # Create it empty so we can open it
        file_path.touch()

    log_daemon(f"Starting log tailer for {file_path.name}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # Go to the end of the file
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.5)
                    continue
                try:
                    entry = json.loads(line.strip())
                    await broadcast({
                        "type": msg_type,
                        "data": entry
                    })
                except Exception as ex:
                    log_daemon(f"Error parsing log line in {file_path.name}: {ex}")
    except asyncio.CancelledError:
        log_daemon(f"Tailer for {file_path.name} cancelled.")
    except Exception as e:
        log_daemon(f"Tailer error for {file_path.name}: {e}")

def get_system_info():
    """Import and call discovery helper to avoid manual parsing."""
    try:
        from netdiscover import get_default_iface_and_gateway
        iface, gateway_ip, local_ip, cidr = get_default_iface_and_gateway()
        return {
            "interface": iface,
            "gateway_ip": gateway_ip,
            "local_ip": local_ip,
            "cidr": cidr
        }
    except Exception as e:
        log_daemon(f"Failed to get system info: {e}")
        return {
            "interface": "unknown",
            "gateway_ip": "unknown",
            "local_ip": "127.0.0.1",
            "cidr": "127.0.0.1/24",
            "error": str(e)
        }

def get_network_info():
    """Returns rich WiFi and network context using iwconfig / nmcli / ip."""
    info = {
        "ssid": None, "bssid": None, "interface": None,
        "frequency": None, "channel": None, "signal_dbm": None,
        "signal_quality": None, "bitrate": None, "security": None,
        "tx_power": None, "local_ip": None, "gateway": None,
        "mode": "unknown"
    }
    try:
        # Get default interface and IP info
        route_out = subprocess.check_output(
            ["ip", "-4", "route", "show", "default"],
            stderr=subprocess.DEVNULL, text=True
        ).strip()
        if route_out:
            parts = route_out.split()
            info["gateway"] = parts[2] if len(parts) > 2 else None
            iface = parts[4] if len(parts) > 4 else None
            info["interface"] = iface
            # Get local IP
            try:
                addr_out = subprocess.check_output(
                    ["ip", "-4", "-o", "addr", "show", "dev", iface],
                    stderr=subprocess.DEVNULL, text=True
                ).strip()
                if addr_out:
                    info["local_ip"] = addr_out.split()[3].split("/")[0]
            except Exception:
                pass
            # Try iwconfig for WiFi info
            try:
                iwconfig_out = subprocess.check_output(
                    ["iwconfig", iface], stderr=subprocess.DEVNULL, text=True
                )
                import re as _re
                ssid_m = _re.search(r'ESSID:"([^"]+)"', iwconfig_out)
                if ssid_m:
                    info["ssid"] = ssid_m.group(1)
                    info["mode"] = "wifi"
                bssid_m = _re.search(r'Access Point: ([0-9A-Fa-f:]{17})', iwconfig_out)
                if bssid_m:
                    info["bssid"] = bssid_m.group(1)
                freq_m = _re.search(r'Frequency:(\S+\s+\S+)', iwconfig_out)
                if freq_m:
                    info["frequency"] = freq_m.group(1).strip()
                bitrate_m = _re.search(r'Bit Rate=(\S+\s+\S+)', iwconfig_out)
                if bitrate_m:
                    info["bitrate"] = bitrate_m.group(1).strip()
                sig_m = _re.search(r'Signal level=(-?\d+)\s*dBm', iwconfig_out)
                if sig_m:
                    info["signal_dbm"] = int(sig_m.group(1))
                qual_m = _re.search(r'Link Quality=(\d+)/(\d+)', iwconfig_out)
                if qual_m:
                    info["signal_quality"] = int(int(qual_m.group(1)) / int(qual_m.group(2)) * 100)
                txpwr_m = _re.search(r'Tx-Power=(\S+)\s+dBm', iwconfig_out)
                if txpwr_m:
                    info["tx_power"] = txpwr_m.group(1) + " dBm"
            except Exception:
                info["mode"] = "ethernet"
            # Try nmcli for security type and channel
            try:
                if info["ssid"]:
                    nmcli_out = subprocess.check_output(
                        ["nmcli", "-t", "-f", "ACTIVE,SSID,SIGNAL,SECURITY,FREQ,CHAN",
                         "device", "wifi"],
                        stderr=subprocess.DEVNULL, text=True
                    )
                    for line in nmcli_out.strip().splitlines():
                        cols = line.split(":")
                        if len(cols) >= 6 and cols[0] == "yes":
                            info["security"] = cols[3] if cols[3] else "Open"
                            info["channel"] = cols[5] if cols[5] else None
                            break
            except Exception:
                pass
    except Exception as e:
        log_daemon(f"get_network_info error: {e}")
    return info


def read_last_lines(file_path, count=50):
    if not file_path.exists():
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Parse only the last N non-empty lines
            parsed = []
            for line in lines[-count:]:
                if line.strip():
                    try:
                        parsed.append(json.loads(line.strip()))
                    except:
                        pass
            return parsed
    except Exception as e:
        log_daemon(f"Error reading last lines of {file_path.name}: {e}")
        return []

async def run_process_reader(process, name):
    """Reads stdout and stderr of a process and broadcasts as terminal output."""
    log_daemon(f"Process reader started for {name} (PID: {process.pid})")
    try:
        while True:
            # We must run this in an executor or use asyncio subprocess
            # Since process was created using subprocess.Popen, let's use a non-blocking read
            # Or run in a thread/executor. An executor loop is simpler.
            line = await asyncio.get_event_loop().run_in_executor(
                None, process.stdout.readline
            )
            if not line:
                break
            text = line.decode("utf-8", errors="ignore").rstrip()
            await broadcast({
                "type": "terminal",
                "data": {
                    "process": name,
                    "text": text
                }
            })
    except Exception as e:
        log_daemon(f"Error reading process output: {e}")
    finally:
        # Wait for process to exit
        await asyncio.get_event_loop().run_in_executor(None, process.wait)
        log_daemon(f"Process {name} exited with code {process.returncode}")
        global active_process, active_process_name
        async with process_lock:
            if active_process == process:
                active_process = None
                active_process_name = None
        await broadcast({
            "type": "status",
            "data": {
                "running": False,
                "process": None,
                "exit_code": process.returncode
            }
        })

async def stop_active_process():
    global active_process, active_process_name
    async with process_lock:
        if active_process:
            log_daemon(f"Stopping active process {active_process_name} (PID: {active_process.pid})")
            # Try gentle SIGTERM first
            active_process.terminate()
            try:
                # Wait up to 3 seconds for exit
                for _ in range(30):
                    if active_process.poll() is not None:
                        break
                    await asyncio.sleep(0.1)
                else:
                    log_daemon(f"Force killing process (PID: {active_process.pid})")
                    active_process.kill()
            except Exception as e:
                log_daemon(f"Error while terminating process: {e}")
            active_process = None
            active_process_name = None
            
            # Run cleanup commands
            log_daemon("Running network state cleanup...")
            cleanup_proc = subprocess.run(
                ["ip", "-s", "neigh", "flush", "all"],
                capture_output=True
            )
            cleanup_proc2 = subprocess.run(
                ["sysctl", "-w", "net.ipv4.ip_forward=0"],
                capture_output=True
            )
            # Remove iptables NAT rules tagged with comment
            rules_proc = subprocess.run(
                ["iptables", "-t", "nat", "-L", "PREROUTING", "--line-numbers", "-n"],
                capture_output=True, text=True
            )
            line_numbers = []
            for line in rules_proc.stdout.splitlines():
                if "mitm-intercept-auto" in line:
                    line_numbers.append(int(line.split()[0]))
            for ln in sorted(line_numbers, reverse=True):
                subprocess.run(["iptables", "-t", "nat", "-D", "PREROUTING", str(ln)], capture_output=True)

            # Clear state file
            from state_manager import clear_state
            clear_state()
            
            log_daemon("Cleanup complete.")

async def handle_action(action, params):
    global active_process, active_process_name
    
    if action == "ping":
        return {"status": "success", "message": "pong"}

    elif action == "get_system_info":
        return {"status": "success", "data": get_system_info()}

    elif action == "get_network_info":
        return {"status": "success", "data": get_network_info()}

    elif action == "get_traffic_stats":
        traffic_history = read_last_lines(TRAFFIC_LOG, 500)
        stats = {
            "total": len(traffic_history),
            "by_method": {},
            "by_protocol": {"http": 0, "https": 0},
            "by_status": {},
            "intercepted": 0,
            "total_bytes": 0,
        }
        for entry in traffic_history:
            m = entry.get("method", "?").upper()
            stats["by_method"][m] = stats["by_method"].get(m, 0) + 1
            proto = entry.get("protocol", "http").lower()
            if proto in stats["by_protocol"]:
                stats["by_protocol"][proto] += 1
            s = str(entry.get("status", "?"))
            s_bucket = s[0] + "xx" if s and s[0].isdigit() else "?"
            stats["by_status"][s_bucket] = stats["by_status"].get(s_bucket, 0) + 1
            if entry.get("intercepted"):
                stats["intercepted"] += 1
            stats["total_bytes"] += entry.get("size", 0) or 0
        return {"status": "success", "stats": stats}

    elif action == "get_config":
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    content = yaml.safe_load(f)
                return {"status": "success", "config": content}
            except Exception as e:
                return {"status": "error", "message": f"Failed to read config: {e}"}
        else:
            return {"status": "error", "message": "mitm-intercept.yml not found"}


    elif action == "save_config":
        config_data = params.get("config", {})
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.safe_dump(config_data, f, default_flow_style=False)
            return {"status": "success", "message": "Config saved successfully"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to save config: {e}"}

    elif action == "scan_network":
        # Scan local network
        sys_info = get_system_info()
        iface = sys_info["interface"]
        cidr = sys_info["cidr"]
        if iface == "unknown" or cidr == "unknown":
            return {"status": "error", "message": "Could not determine network interface/subnet"}
        
        log_daemon(f"Performing subnet ARP scan on {iface} / {cidr}...")
        try:
            from netdiscover import scan_subnet
            # Run scan in thread pool since scapy srp is blocking
            hosts = await asyncio.get_event_loop().run_in_executor(
                None, scan_subnet, iface, cidr
            )
            return {"status": "success", "hosts": hosts}
        except Exception as e:
            return {"status": "error", "message": f"Scan failed: {e}"}

    elif action == "start_mitm":
        async with process_lock:
            if active_process:
                return {"status": "error", "message": f"Another process ({active_process_name}) is already running"}
            
            targets = params.get("targets", "")
            interface = params.get("interface", "")
            dns_redirect = params.get("dns_redirect", "")
            
            cmd = [sys.executable, "main_cli.py", "start", "-y"]
            if targets:
                cmd.extend(["--targets", targets])
            if interface:
                cmd.extend(["--interface", interface])
            if dns_redirect:
                cmd.extend(["--dns-redirect", dns_redirect])
            
            log_daemon(f"Starting MITM: {' '.join(cmd)}")
            try:
                # We spawn subprocess with pipe for stdout/stderr
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.PIPE
                )
                active_process = proc
                active_process_name = "mitm"
                
                # Start output reader task
                asyncio.create_task(run_process_reader(proc, "mitm"))
                return {"status": "success", "message": "MITM lab started"}
            except Exception as e:
                log_daemon(f"Failed to start MITM: {e}")
                return {"status": "error", "message": str(e)}

    elif action == "stop_mitm" or action == "stop_all":
        await stop_active_process()
        return {"status": "success", "message": "All attacks stopped and cleaned up"}

    elif action == "get_status":
        from state_manager import load_state
        state = load_state()
        return {
            "status": "success",
            "data": {
                "running": active_process is not None,
                "process": active_process_name,
                "pid": active_process.pid if active_process else None,
                "state": state
            }
        }

    # WiFi & Phase 1 Actions
    elif action == "start_ap":
        async with process_lock:
            if active_process:
                return {"status": "error", "message": f"Another process ({active_process_name}) is already running"}
            
            interface = params.get("interface", "wlan0")
            ssid = params.get("ssid", "Starbucks_WiFi")
            channel = params.get("channel", 6)
            
            cmd = [sys.executable, "main_cli.py", "phase1", "ap-mode", "--interface", interface, "--ssid", ssid, "--channel", str(channel), "-y"]
            log_daemon(f"Starting Rogue AP: {' '.join(cmd)}")
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                active_process = proc
                active_process_name = "ap"
                asyncio.create_task(run_process_reader(proc, "ap"))
                return {"status": "success", "message": "Rogue AP started"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

    elif action == "scan_wifi":
        async with process_lock:
            if active_process:
                return {"status": "error", "message": f"Another process ({active_process_name}) is already running"}
            
            interface = params.get("interface", "wlan0")
            cmd = [sys.executable, "main_cli.py", "phase1", "scan-networks", "--interface", interface]
            log_daemon(f"Starting WiFi Scan: {' '.join(cmd)}")
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                active_process = proc
                active_process_name = "scan"
                asyncio.create_task(run_process_reader(proc, "scan"))
                return {"status": "success", "message": "WiFi scanning started"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

    elif action == "start_deauth":
        async with process_lock:
            if active_process:
                return {"status": "error", "message": f"Another process ({active_process_name}) is already running"}
            
            interface = params.get("interface", "wlan0")
            target_mac = params.get("target_mac", "")
            gateway_mac = params.get("gateway_mac", "")
            ssid = params.get("ssid", "")
            
            if not target_mac:
                return {"status": "error", "message": "Target MAC address required"}
            
            cmd = [sys.executable, "main_cli.py", "phase1", "deauth", "--interface", interface, "--target-mac", target_mac, "-y"]
            if gateway_mac:
                cmd.extend(["--gateway-mac", gateway_mac])
            if ssid:
                cmd.extend(["--ssid", ssid])
                
            log_daemon(f"Starting WiFi Deauth: {' '.join(cmd)}")
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                active_process = proc
                active_process_name = "deauth"
                asyncio.create_task(run_process_reader(proc, "deauth"))
                return {"status": "success", "message": "WiFi deauth started"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

    elif action == "scan_website":
        target = params.get("target", "")
        if not target:
            return {"status": "error", "message": "Target website URL is required"}
        
        log_daemon(f"Running vulnerability audit for target: {target}...")
        try:
            from recon_engine import ReconEngine
            engine = ReconEngine()
            
            # Execute the scan in a thread pool executor
            findings = await asyncio.get_event_loop().run_in_executor(
                None, engine.scan, target
            )
            
            db_compromise = findings.get("database_compromise", None)
            
            # Formulate the SQL injection dump for the GUI
            sqli_dump = []
            if db_compromise and "users_table" in db_compromise:
                for s in db_compromise["users_table"]["sample"]:
                    sqli_dump.append({
                        "id": s["id"],
                        "username": f"{s['username']} ({s['email']})",
                        "pass_hash": s["password_hash"]
                    })
            
            # Formulate the keys for the exposed secrets
            exposed_keys = []
            for sec in findings.get("secrets", []):
                exposed_keys.append({
                    "type": sec.get("type", "API Key"),
                    "key": sec.get("evidence", "Found in public repository")
                })
            
            # Convert Vulnerability objects to serializable dicts
            serialized_vulns = []
            for idx, v in enumerate(findings.get("vulnerabilities", [])):
                vuln_type_str = v.vuln_type.value if hasattr(v.vuln_type, 'value') else str(v.vuln_type)
                
                vuln_dict = {
                    "id": f"vuln-{idx+1:02d}",
                    "severity": v.severity.lower(),
                    "title": v.description,
                    "location": v.evidence,
                    "description": f"Vulnerability detected by ReconEngine. Type: {vuln_type_str}. Tested on target: {v.target}.",
                    "remediation": "Mitigate by implementing secure coding standards and updating software.",
                    "exploit_simulated": v.exploitation_possible
                }
                
                if vuln_type_str == "sql_injection" and sqli_dump:
                    vuln_dict["dump"] = sqli_dump
                
                if vuln_type_str == "exposed_secret" and exposed_keys:
                    vuln_dict["keys"] = exposed_keys
                
                serialized_vulns.append(vuln_dict)
            
            # Fallbacks to ensure GUI compatibility
            if sqli_dump and serialized_vulns:
                has_dump = any("dump" in v for v in serialized_vulns)
                if not has_dump:
                    serialized_vulns[0]["dump"] = sqli_dump

            if exposed_keys and serialized_vulns:
                has_keys = any("keys" in v for v in serialized_vulns)
                if not has_keys:
                    for v in serialized_vulns:
                        if "secret" in v["title"].lower() or "config" in v["title"].lower():
                            v["keys"] = exposed_keys
                            break
                    else:
                        serialized_vulns[0]["keys"] = exposed_keys
            
            critical_cnt = sum(1 for v in serialized_vulns if v["severity"] == "critical")
            high_cnt = sum(1 for v in serialized_vulns if v["severity"] == "high")
            medium_cnt = sum(1 for v in serialized_vulns if v["severity"] == "medium")
            low_cnt = len(serialized_vulns) - (critical_cnt + high_cnt + medium_cnt)
            
            report_text = engine.display_report()
            
            return {
                "status": "success",
                "target": target,
                "score": max(100 - len(serialized_vulns) * 10, 10),
                "stats": {
                    "critical": critical_cnt,
                    "high": high_cnt,
                    "medium": medium_cnt,
                    "low": max(low_cnt, 0)
                },
                "vulnerabilities": serialized_vulns,
                "database_compromise": db_compromise,
                "report_text": report_text
            }
        except Exception as e:
            log_daemon(f"Failed to scan website: {e}")
            return {"status": "error", "message": str(e)}

    elif action == "start_phishing":
        template = params.get("template", "gmail")
        redirect = params.get("redirect", "https://mail.google.com")
        phish_state = {
            "active": True,
            "template": template,
            "redirect_url": redirect
        }
        try:
            with open("phishing_state.json", "w") as f:
                json.dump(phish_state, f)
            log_daemon(f"Phishing active. Template: {template}, Redirect: {redirect}")
            return {"status": "success", "message": f"Phishing portal deployed using {template} template"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to start phishing: {e}"}

    elif action == "stop_phishing":
        phish_state = {
            "active": False
        }
        try:
            with open("phishing_state.json", "w") as f:
                json.dump(phish_state, f)
            log_daemon("Phishing portal disabled.")
            return {"status": "success", "message": "Phishing portal disabled"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to stop phishing: {e}"}

    else:
        return {"status": "error", "message": f"Unknown action: {action}"}

def is_client_authorized(websocket):
    if not DAEMON_AUTH_TOKEN:
        return True

    path = getattr(websocket, "path", "") or ""
    token = parse_qs(urlparse(path).query).get("token", [""])[0]
    return secrets.compare_digest(token, DAEMON_AUTH_TOKEN)

async def ws_handler(websocket):
    if not is_client_authorized(websocket):
        log_daemon(f"Rejected unauthenticated client: {websocket.remote_address}")
        await websocket.close(code=4001, reason="Unauthorized")
        return

    log_daemon(f"Client connected: {websocket.remote_address}")
    connected_clients.add(websocket)
    
    # Send initial setup state & logs
    sys_info = get_system_info()
    net_info = get_network_info()
    traffic_history = read_last_lines(TRAFFIC_LOG, 100)
    creds_history = read_last_lines(CREDS_LOG, 50)
    
    from state_manager import load_state
    state = load_state()
    
    phish_state = {"active": False}
    if os.path.exists("phishing_state.json"):
        try:
            with open("phishing_state.json", "r") as f:
                phish_state = json.load(f)
        except Exception:
            pass

    initial_payload = {
        "type": "init",
        "data": {
            "sys_info": sys_info,
            "net_info": net_info,
            "running": active_process is not None,
            "process": active_process_name,
            "state": state,
            "traffic_history": traffic_history,
            "creds_history": creds_history,
            "phish_state": phish_state
        }
    }
    await websocket.send(json.dumps(initial_payload))

    
    try:
        async for message in websocket:
            try:
                req = json.loads(message)
                action = req.get("action")
                params = req.get("params", {})
                req_id = req.get("id")
                
                res = await handle_action(action, params)
                if req_id is not None:
                    res["id"] = req_id
                
                await websocket.send(json.dumps(res))
            except Exception as e:
                log_daemon(f"Error handling message: {e}")
                await websocket.send(json.dumps({"status": "error", "message": str(e)}))
    except websockets.exceptions.ConnectionClosed as e:
        log_daemon(f"Client disconnected: {websocket.remote_address} - {e}")
    finally:
        connected_clients.remove(websocket)

async def main():
    log_daemon(f"Starting privileged backend daemon on ws://{HOST}:{PORT}")
    
    # Start log tailing background tasks
    traffic_task = asyncio.create_task(tail_file(TRAFFIC_LOG, "traffic"))
    creds_task = asyncio.create_task(tail_file(CREDS_LOG, "creds"))
    heartbeat_task = asyncio.create_task(heartbeat_loop())
    
    async with websockets.serve(ws_handler, HOST, PORT):
        try:
            await asyncio.Future()  # run forever
        except asyncio.CancelledError:
            pass
        finally:
            log_daemon("Shutting down daemon...")
            traffic_task.cancel()
            creds_task.cancel()
            heartbeat_task.cancel()
            await stop_active_process()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDaemon terminated by user.")
