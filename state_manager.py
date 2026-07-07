"""
State management for NEON-SHIELD.

Saves and restores execution state (spoofed IPs, active iptables rules, etc.)
for crash recovery and clean shutdown.
"""
import json
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

STATE_DIR = os.path.expanduser("~/.neon-shield")
STATE_FILE = os.path.join(STATE_DIR, "state.json")


def ensure_state_dir():
    """Create state directory if needed."""
    os.makedirs(STATE_DIR, exist_ok=True)


def save_state(
    spoofed_ips: List[str],
    active_iptables_rules: List[str],
    gateway_ip: str,
    interface: str,
) -> None:
    """Save execution state for recovery."""
    ensure_state_dir()
    state = {
        "spoofed_ips": spoofed_ips,
        "active_iptables_rules": active_iptables_rules,
        "gateway_ip": gateway_ip,
        "interface": interface,
    }
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        logger.debug(f"Saved state to {STATE_FILE}")
    except Exception as e:
        logger.error(f"Failed to save state: {e}")


def load_state() -> Optional[Dict]:
    """Load execution state for recovery."""
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
        logger.debug(f"Loaded state from {STATE_FILE}")
        return state
    except Exception as e:
        logger.error(f"Failed to load state: {e}")
        return None


def clear_state() -> None:
    """Clear saved state (called after successful shutdown)."""
    if os.path.exists(STATE_FILE):
        try:
            os.remove(STATE_FILE)
            logger.debug("Cleared state file")
        except Exception as e:
            logger.error(f"Failed to clear state: {e}")
