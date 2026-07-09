"""
Transparent-redirect controller for MITM-INTERCEPT auto mode (Linux only).

Enables IP forwarding and installs iptables NAT rules that redirect
plaintext HTTP (port 80) and HTTPS (port 443) traffic passing through this
host into the proxy's transparent listener ports, so devices whose traffic
is routed through this machine (e.g. via ARP spoofing) are intercepted
without any manual per-device proxy configuration.

All changes made here are tracked and reverted by teardown().
"""
import subprocess


RULE_COMMENT = "mitm-intercept-auto"


def _run(args, check=True):
    return subprocess.run(args, capture_output=True, text=True, check=check)


def _get_ip_forward():
    result = _run(["sysctl", "-n", "net.ipv4.ip_forward"])
    return result.stdout.strip() == "1"


class TransparentRedirect:
    def __init__(self, http_port, https_port, dns_port=None):
        self.http_port = http_port
        self.https_port = https_port
        self.dns_port = dns_port
        self._prev_ip_forward = None
        self._active = False

    def setup(self):
        self._prev_ip_forward = _get_ip_forward()
        _run(["sysctl", "-w", "net.ipv4.ip_forward=1"])

        rules = [
            ["-p", "tcp", "--dport", "80", "-m", "comment", "--comment", RULE_COMMENT,
             "-j", "REDIRECT", "--to-port", str(self.http_port)],
            ["-p", "tcp", "--dport", "443", "-m", "comment", "--comment", RULE_COMMENT,
             "-j", "REDIRECT", "--to-port", str(self.https_port)],
        ]
        if self.dns_port:
            rules.append(
                ["-p", "udp", "--dport", "53", "-m", "comment", "--comment", RULE_COMMENT,
                 "-j", "REDIRECT", "--to-port", str(self.dns_port)]
            )
        for rule in rules:
            _run(["iptables", "-t", "nat", "-A", "PREROUTING", *rule])

        self._active = True
        msg = f"[Transparent] IP forwarding enabled, redirecting 80->{self.http_port}, 443->{self.https_port}"
        if self.dns_port:
            msg += f", udp/53->{self.dns_port}"
        print(msg)

    def teardown(self):
        if not self._active:
            return
        # Remove only the rules we tagged, in case other rules exist.
        result = _run(["iptables", "-t", "nat", "-L", "PREROUTING", "--line-numbers", "-n"], check=False)
        line_numbers = []
        for line in result.stdout.splitlines():
            if RULE_COMMENT in line:
                line_numbers.append(int(line.split()[0]))

        for line_number in sorted(line_numbers, reverse=True):
            _run(["iptables", "-t", "nat", "-D", "PREROUTING", str(line_number)], check=False)

        if self._prev_ip_forward is not None and not self._prev_ip_forward:
            _run(["sysctl", "-w", "net.ipv4.ip_forward=0"], check=False)

        self._active = False
        print("[Transparent] iptables rules removed and IP forwarding state restored.")
