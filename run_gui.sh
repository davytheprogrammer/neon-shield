#!/bin/bash
# Startup script for NEON-SHIELD GUI & Daemon

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${CYAN}⚡ NEON-SHIELD GUI Launcher ⚡${NC}"
echo -e "======================================"

# Ensure we're in the repository root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# 1. Start the privileged backend daemon
echo -e "\n${YELLOW}[*] Starting Privileged Background Daemon...${NC}"
echo -e "This requires root privileges to configure network interfaces, iptables, and scapy."
export NEON_SHIELD_DAEMON_URL="ws://127.0.0.1:8765"

# Check if daemon is already running
if pgrep -f "python3 daemon.py" > /dev/null; then
    echo -e "${GREEN}[✓] Daemon is already running.${NC}"
    export NEON_SHIELD_DAEMON_TOKEN=""
else
    DAEMON_TOKEN=$(python3 -c 'import secrets; print(secrets.token_hex(16))')
    export NEON_SHIELD_DAEMON_TOKEN="$DAEMON_TOKEN"

    # Launch daemon in background with sudo
    sudo NEON_SHIELD_DAEMON_TOKEN="$DAEMON_TOKEN" python3 daemon.py &
    DAEMON_PID=$!
    
    # Wait to ensure daemon binds successfully
    sleep 2
    
    # Check if daemon started successfully
    if ps -p $DAEMON_PID > /dev/null; then
        echo -e "${GREEN}[✓] Daemon started successfully (PID: $DAEMON_PID).${NC}"
        # Set trap to kill daemon on script exit
        trap "echo -e '\n${RED}[*] Stopping daemon...${NC}'; sudo kill $DAEMON_PID; exit" INT TERM EXIT
    else
        echo -e "${RED}[✗] Failed to start daemon. Please check logs/daemon.log${NC}"
        exit 1
    fi
fi

# 2. Start the Tauri GUI Application
echo -e "\n${YELLOW}[*] Starting Tauri Desktop Client (User Space)...${NC}"
cd gui

# Check if npm dependencies are installed (node_modules exists)
if [ ! -d "node_modules" ]; then
    echo -e "${CYAN}[*] Installing Node dependencies...${NC}"
    npm install
fi

# Run Tauri dev server
npm run tauri dev

echo -e "\n${GREEN}[✓] Exiting GUI Launcher.${NC}"
