"""
Local network discovery helpers for NEON-SHIELD auto mode.

Uses scapy to figure out which interface/gateway/subnet this host is on,
and to ARP-scan the local subnet for live hosts. Linux-focused (relies on
`ip route` for gateway/interface detection, which is what the ARP spoofing
and iptables transparent-redirect features also require).
"""
import ipaddress
import subprocess

from scapy.all import ARP, Ether, srp, conf, get_if_hwaddr


def get_default_iface_and_gateway():
    """Returns (iface, gateway_ip, local_ip) for the default route."""
    result = subprocess.run(
        ["ip", "-4", "route", "show", "default"],
        capture_output=True, text=True, check=True,
    )
    line = result.stdout.strip().splitlines()[0]
    parts = line.split()
    gateway_ip = parts[2]
    iface = parts[4]

    addr_result = subprocess.run(
        ["ip", "-4", "-o", "addr", "show", "dev", iface],
        capture_output=True, text=True, check=True,
    )
    # Example line: "2: wlp2s0    inet 192.168.100.54/24 brd ... scope global ..."
    addr_line = addr_result.stdout.strip().splitlines()[0]
    cidr = addr_line.split()[3]

    local_ip = cidr.split("/")[0]
    return iface, gateway_ip, local_ip, cidr


def scan_subnet(iface, cidr, timeout=1.5):
    """
    ARP-scans every host address in `cidr` on `iface`.
    Returns a list of dicts: {"ip": ..., "mac": ...}
    """
    network = ipaddress.ip_network(cidr, strict=False)
    targets = str(network)

    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    arp = ARP(pdst=targets)
    packet = ether / arp

    answered, _ = srp(packet, timeout=timeout, iface=iface, filter="arp", verbose=False)

    hosts = []
    for _, received in answered:
        hosts.append({"ip": received.psrc, "mac": received.hwsrc})
    return hosts


def get_own_mac(iface):
    return get_if_hwaddr(iface)


if __name__ == "__main__":
    iface, gateway_ip, local_ip, cidr = get_default_iface_and_gateway()
    print(f"[Discover] iface={iface} local_ip={local_ip} gateway={gateway_ip} cidr={cidr}")
    print("[Discover] Scanning subnet, this can take a few seconds...")
    hosts = scan_subnet(iface, cidr)
    for h in hosts:
        tag = ""
        if h["ip"] == gateway_ip:
            tag = " (gateway)"
        elif h["ip"] == local_ip:
            tag = " (this host)"
        print(f"  {h['ip']:<16} {h['mac']}{tag}")
    print(f"[Discover] Found {len(hosts)} live host(s).")
