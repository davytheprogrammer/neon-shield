"""
WiFi Network Scanner for MITM-INTERCEPT Phase 1.

Scans nearby WiFi networks and detects vulnerabilities.
Shows which networks use weak encryption and which devices are searching for networks.

⚠️ EDUCATIONAL USE ONLY — See README.md for legal disclaimer.
"""
import subprocess
import json
import logging
import re
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class WiFiNetwork:
    """WiFi network information."""
    ssid: str
    bssid: str
    channel: int
    signal_strength: int
    encryption: str
    cipher: str
    vulnerability: str = ""

    def display(self) -> str:
        """Format for display."""
        vuln_icon = "🔴" if "VULNERABLE" in self.vulnerability else "🟢"
        return f"{vuln_icon} {self.ssid:20} | CH{self.channel:2} | {self.encryption:15} | Signal: {self.signal_strength:3}dBm"


class WiFiScanner:
    """
    Scans and analyzes nearby WiFi networks.

    ⚠️ WARNING: Passive scanning is legal, but targeting specific networks
    for attack requires authorization.
    """

    def __init__(self, interface: str):
        """
        Initialize scanner.

        Args:
            interface: WiFi interface to use for scanning (e.g., 'wlan0')
        """
        self.interface = interface
        self.networks: List[WiFiNetwork] = []

    def scan(self, duration: int = 30) -> bool:
        """
        Scan for nearby WiFi networks.

        Args:
            duration: Scan duration in seconds

        Returns:
            True if scan completed successfully
        """
        logger.info(f"Scanning for WiFi networks on {self.interface} ({duration}s)...")

        try:
            # Use iw to scan
            result = subprocess.run(
                ["sudo", "iw", "dev", self.interface, "scan"],
                capture_output=True,
                text=True,
                timeout=duration + 5,
                check=False
            )

            if result.returncode != 0:
                logger.error(f"Scan failed: {result.stderr}")
                return False

            self._parse_scan_results(result.stdout)
            return True

        except Exception as e:
            logger.error(f"Scan error: {e}")
            return False

    def _parse_scan_results(self, output: str) -> None:
        """Parse iwconfig scan output."""
        networks = {}
        current_network = None

        for line in output.split("\n"):
            if "SSID:" in line:
                ssid = line.split("SSID: ", 1)[1].strip()
                current_network = {"ssid": ssid}
            elif "BSSID:" in line and current_network:
                current_network["bssid"] = line.split("BSSID: ", 1)[1].strip()
            elif "freq:" in line and current_network:
                freq_str = line.split("freq: ", 1)[1].strip()
                current_network["channel"] = self._freq_to_channel(int(freq_str))
            elif "signal:" in line and current_network:
                signal_str = line.split("signal: ", 1)[1].split(" ")[0]
                current_network["signal"] = int(signal_str)
            elif "capability:" in line and current_network:
                caps = line.split("capability: ", 1)[1].strip()
                current_network["encryption"] = self._parse_encryption(caps)

        # Convert to WiFiNetwork objects
        for net_data in networks.values():
            if "ssid" in net_data:
                vuln = self._check_vulnerability(net_data)
                net = WiFiNetwork(
                    ssid=net_data.get("ssid", ""),
                    bssid=net_data.get("bssid", ""),
                    channel=net_data.get("channel", 0),
                    signal_strength=net_data.get("signal", 0),
                    encryption=net_data.get("encryption", "Unknown"),
                    cipher=net_data.get("cipher", ""),
                    vulnerability=vuln
                )
                self.networks.append(net)

    def _freq_to_channel(self, freq_mhz: int) -> int:
        """Convert frequency to WiFi channel."""
        if freq_mhz >= 2412 and freq_mhz <= 2484:
            return (freq_mhz - 2407) // 5
        elif freq_mhz >= 5000 and freq_mhz <= 6000:
            return (freq_mhz - 5000) // 5
        return 0

    def _parse_encryption(self, capabilities: str) -> str:
        """Parse encryption from capabilities string."""
        if "WPA3" in capabilities:
            return "WPA3"
        elif "WPA2" in capabilities or "RSN" in capabilities:
            return "WPA2"
        elif "WPA" in capabilities:
            return "WPA"
        elif "WEP" in capabilities:
            return "WEP"
        else:
            return "OPEN"

    def _check_vulnerability(self, network: dict) -> str:
        """Check network for vulnerabilities."""
        encryption = network.get("encryption", "")

        if encryption == "OPEN":
            return "🔴 VULNERABLE: No encryption"
        elif encryption == "WEP":
            return "🔴 VULNERABLE: WEP (broken)"
        elif encryption == "WPA":
            return "🟡 WEAK: WPA (outdated)"
        elif encryption == "WPA2":
            return "🟢 Acceptable: WPA2"
        elif encryption == "WPA3":
            return "🟢 Secure: WPA3"

        return ""

    def display_results(self) -> None:
        """Display scan results in a formatted table."""
        if not self.networks:
            logger.warning("No networks found")
            return

        logger.info(f"\n📡 Found {len(self.networks)} network(s):\n")

        vulnerable_count = 0
        for net in sorted(self.networks, key=lambda x: x.signal_strength, reverse=True):
            print(net.display())
            if "VULNERABLE" in net.vulnerability or "WEAK" in net.vulnerability:
                vulnerable_count += 1

        logger.info(f"\n⚠️  {vulnerable_count} network(s) with vulnerabilities")
        logger.info("\n💡 Recommendation: Use WPA3 encryption with strong password")
        logger.info("💡 Enable: Hide SSID broadcast (makes discovery harder)")
        logger.info("💡 Never: Connect to open networks without VPN")

    def get_vulnerable_networks(self) -> List[WiFiNetwork]:
        """Return list of vulnerable networks."""
        return [n for n in self.networks if "VULNERABLE" in n.vulnerability]


def check_scanner_requirements() -> tuple[bool, str]:
    """
    Check if system has requirements for WiFi scanning.

    Returns:
        (can_run: bool, message: str)
    """
    try:
        subprocess.run(["which", "iw"], capture_output=True, check=True)
        return True, "Scanner ready"
    except subprocess.CalledProcessError:
        return False, "Missing 'iw' tool. Install with: sudo apt-get install iw"
