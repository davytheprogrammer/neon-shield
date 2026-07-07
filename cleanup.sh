#!/bin/bash
# Emergency cleanup script for NEON-SHIELD
# Restores ARP tables and removes iptables rules if NEON-SHIELD crashes

set -e

echo "⚠️  NEON-SHIELD Emergency Cleanup"
echo "=================================="
echo ""
echo "This script will attempt to restore your network to normal state."
echo ""

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

read -p "Continue? (yes/no): " -n 3 -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Cleanup cancelled."
    exit 1
fi

echo "[*] Disabling IP forwarding..."
sysctl -w net.ipv4.ip_forward=0 > /dev/null 2>&1 || true

echo "[*] Removing iptables NAT rules..."
iptables -t nat -L PREROUTING --line-numbers -n | grep "neon-shield-auto" | awk '{print $1}' | sort -rn | while read line; do
    iptables -t nat -D PREROUTING $line > /dev/null 2>&1 || true
done

echo "[*] Flushing ARP cache..."
ip -s neigh flush all > /dev/null 2>&1 || true

echo "[*] Clearing NEON-SHIELD state file..."
rm -f ~/.neon-shield/state.json

echo ""
echo "✓ Cleanup complete. Your network should be restored to normal."
echo ""
