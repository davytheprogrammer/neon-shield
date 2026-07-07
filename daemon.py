#!/usr/bin/env python3
import asyncio
import json
import os
import sys
import subprocess
import threading
import time
import yaml
from pathlib import Path
import websockets

# Constants
HOST = "127.0.0.1"
PORT = 8765
CONFIG_PATH = Path("neon-shield.yml")
LOGS_DIR = Path("logs")
TRAFFIC_LOG = LOGS_DIR / "traffic.jsonl"
CREDS_LOG = LOGS_DIR / "credentials.jsonl"
DAEMON_LOG = LOGS_DIR / "daemon.log"

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
    # Create list of tasks to run concurrently
    tasks = [asyncio.create_task(client.send(message_str)) for client in connected_clients]
    if tasks:
        await asyncio.wait(tasks)

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
                if "neon-shield-auto" in line:
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

    elif action == "get_config":
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    content = yaml.safe_load(f)
                return {"status": "success", "config": content}
            except Exception as e:
                return {"status": "error", "message": f"Failed to read config: {e}"}
        else:
            return {"status": "error", "message": "neon-shield.yml not found"}

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

    else:
        return {"status": "error", "message": f"Unknown action: {action}"}

async def ws_handler(websocket):
    log_daemon(f"Client connected: {websocket.remote_address}")
    connected_clients.add(websocket)
    
    # Send initial setup state & logs
    sys_info = get_system_info()
    traffic_history = read_last_lines(TRAFFIC_LOG, 100)
    creds_history = read_last_lines(CREDS_LOG, 50)
    
    from state_manager import load_state
    state = load_state()
    
    initial_payload = {
        "type": "init",
        "data": {
            "sys_info": sys_info,
            "running": active_process is not None,
            "process": active_process_name,
            "state": state,
            "traffic_history": traffic_history,
            "creds_history": creds_history
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
    
    async with websockets.serve(ws_handler, HOST, PORT):
        # Keep running forever
        try:
            await asyncio.Future()  # run forever
        except asyncio.CancelledError:
            pass
        finally:
            log_daemon("Shutting down daemon...")
            traffic_task.cancel()
            creds_task.cancel()
            await stop_active_process()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDaemon terminated by user.")
