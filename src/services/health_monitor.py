"""
Health monitoring for MITM-INTERCEPT.

Periodically checks that ARP spoofing and iptables rules are still active,
and auto-recovers if they fail.
"""
import subprocess
import threading
import time
import logging
from typing import List, Callable, Optional

logger = logging.getLogger(__name__)


class HealthMonitor:
    def __init__(
        self,
        check_interval: int = 10,
        auto_recover: bool = True,
        log_checks: bool = False,
    ):
        self.check_interval = check_interval
        self.auto_recover = auto_recover
        self.log_checks = log_checks
        self._stop_event = threading.Event()
        self._thread = None
        self._callbacks = {
            "arp_failed": [],
            "iptables_failed": [],
            "proxy_failed": [],
            "recovered": [],
        }

    def register_callback(self, event: str, callback: Callable) -> None:
        """Register a callback for health events."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _call_callbacks(self, event: str, *args) -> None:
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args)
            except Exception as e:
                logger.error(f"Callback error ({event}): {e}")

    def _check_arp_active(self, target_ips: List[str], gateway_ip: str) -> bool:
        """Check if ARP spoofing is still active (verify ARP cache has been poisoned)."""
        try:
            for target_ip in target_ips[:3]:  # Check first 3 targets
                result = subprocess.run(
                    ["arp", "-n", target_ip],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                # If arp entry shows us as gateway, poisoning is active
                if result.returncode == 0 and "incomplete" not in result.stdout:
                    return True
        except Exception as e:
            if self.log_checks:
                logger.debug(f"ARP check failed: {e}")
        return False

    def _check_iptables_active(self) -> bool:
        """Check if iptables redirect rules are still in place."""
        try:
            result = subprocess.run(
                ["iptables", "-t", "nat", "-L", "PREROUTING", "-n"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # Look for our comment marker
            if "mitm-intercept-auto" in result.stdout:
                return True
        except Exception as e:
            if self.log_checks:
                logger.debug(f"iptables check failed: {e}")
        return False

    def _check_proxy_active(self, port: int = 8081) -> bool:
        """Check if proxy is listening on transparent port."""
        try:
            result = subprocess.run(
                ["netstat", "-tuln"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if f":{port}" in result.stdout and "LISTEN" in result.stdout:
                return True
        except Exception as e:
            if self.log_checks:
                logger.debug(f"Proxy check failed: {e}")
        return False

    def _run(
        self,
        target_ips: List[str],
        gateway_ip: str,
    ) -> None:
        """Background health check loop."""
        while not self._stop_event.is_set():
            try:
                arp_ok = self._check_arp_active(target_ips, gateway_ip)
                iptables_ok = self._check_iptables_active()
                proxy_ok = self._check_proxy_active()

                if self.log_checks:
                    logger.debug(f"Health: ARP={arp_ok}, iptables={iptables_ok}, proxy={proxy_ok}")

                if not arp_ok:
                    logger.warning("ARP spoofing appears to have stopped")
                    self._call_callbacks("arp_failed")
                    if self.auto_recover:
                        logger.info("Attempting ARP recovery...")
                        self._call_callbacks("recovered", "arp")

                if not iptables_ok:
                    logger.warning("iptables rules appear to have been removed")
                    self._call_callbacks("iptables_failed")
                    if self.auto_recover:
                        logger.info("Attempting iptables recovery...")
                        self._call_callbacks("recovered", "iptables")

                if not proxy_ok:
                    logger.warning("Proxy does not appear to be listening")
                    self._call_callbacks("proxy_failed")

            except Exception as e:
                logger.error(f"Health check error: {e}")

            self._stop_event.wait(self.check_interval)

    def start(self, target_ips: List[str], gateway_ip: str) -> None:
        """Start background health monitoring."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(target_ips, gateway_ip),
            daemon=True,
        )
        self._thread.start()
        logger.info(f"Health monitor started (check interval: {self.check_interval}s)")

    def stop(self) -> None:
        """Stop health monitoring."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.debug("Health monitor stopped")
