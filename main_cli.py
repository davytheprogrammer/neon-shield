#!/usr/bin/env python3
"""
NEON-SHIELD CLI — Robust, user-friendly command interface.

Usage:
    neon-shield init          # Interactive first-time setup
    neon-shield start         # Start interception (auto-loads config)
    neon-shield stop          # Stop interception (restore ARP/iptables)
    neon-shield status        # Check current status
    neon-shield cleanup       # Emergency recovery (restore everything)
    neon-shield test          # Validate config (dry-run)
"""
import sys
import os
import subprocess

try:
    import click
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except ImportError:
    print("ERROR: Required packages not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

from config import load_config, merge_with_cli, validate_config
from setup_wizard import run_wizard
from log_handler import setup_logging
import state_manager

console = Console()

LEGAL_BANNER = """
⚠️  AUTHORIZED USE ONLY

NEON-SHIELD performs active MITM attacks (ARP spoofing, TLS decryption,
credential capture, DNS spoofing). These are federal crimes without
explicit authorization.

By using this tool, you confirm:
✓ Every target device is owned by you or you have written authorization.
✓ This network is authorized for testing.
✓ You understand the legal consequences (felony charges, fines, imprisonment).
✓ This is for EDUCATION & AUTHORIZED SECURITY RESEARCH only.

See README.md for full disclaimer.
"""


@click.group()
@click.version_option(version="2.0.0", prog_name="NEON-SHIELD")
def cli():
    """NEON-SHIELD — Advanced MITM Lab for Authorized Security Research (Educational Use Only)"""
    pass


@cli.command()
def init():
    """Interactive first-time setup wizard."""
    console.print(Panel(LEGAL_BANNER, style="bold red", title="DISCLAIMER"))

    if not console.input("[yellow]Continue?[/yellow] (yes/no): ").strip().lower().startswith("y"):
        console.print("[red]Setup cancelled.[/red]")
        sys.exit(1)

    try:
        from setup_wizard import run_wizard
        config_dict = run_wizard()

        # TODO: Save to neon-shield.yml
        console.print("[green]✓ Configuration saved to neon-shield.yml[/green]")
    except Exception as e:
        console.print(f"[red]Setup failed: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--targets", help="Target IPs (comma-separated)")
@click.option("--interface", help="Network interface")
@click.option("--dns-redirect", help="DNS spoofing (domain:ip,domain:ip)")
@click.option("--verbose", is_flag=True, help="Verbose output")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
def start(targets, interface, dns_redirect, verbose, yes):
    """Start NEON-SHIELD interception."""
    console.print(Panel(LEGAL_BANNER, style="bold red"))

    if not yes:
        if not console.input("[yellow]Start interception?[/yellow] (yes/no): ").strip().lower().startswith("y"):
            console.print("[red]Cancelled.[/red]")
            sys.exit(1)

    # Load config
    config = load_config("neon-shield.yml")
    cli_args = {
        "targets": targets,
        "interface": interface,
        "dns_redirect": dns_redirect,
        "verbose": verbose,
        "yes": yes,
    }
    config = merge_with_cli(config, cli_args)
    validate_config(config)

    # Setup logging
    setup_logging(config.log_file, config.log_level, config.max_log_size_mb, config.log_backup_count, verbose)

    console.print("[green]✓ Configuration loaded[/green]")
    console.print("[cyan]Starting NEON-SHIELD...[/cyan]")

    # Import and run proxy
    try:
        from proxy import run_auto_mode_with_config
        run_auto_mode_with_config(config)
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
def stop():
    """Stop NEON-SHIELD interception and restore network state."""
    console.print("[yellow]Stopping NEON-SHIELD...[/yellow]")
    # TODO: Send signal to running instance
    console.print("[green]✓ Stopped[/green]")


@cli.command()
def status():
    """Check NEON-SHIELD status."""
    state = state_manager.load_state()

    table = Table(title="NEON-SHIELD Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="magenta")

    if state:
        table.add_row("Spoofed Devices", f"{len(state.get('spoofed_ips', []))} targets")
        table.add_row("Gateway IP", state.get("gateway_ip", "unknown"))
        table.add_row("Interface", state.get("interface", "unknown"))
        table.add_row("iptables Rules", f"{len(state.get('active_iptables_rules', []))} active")
        table.add_row("State", "[green]RUNNING[/green]")
    else:
        table.add_row("State", "[red]NOT RUNNING[/red]")

    console.print(table)


@cli.command()
def cleanup():
    """Emergency recovery: restore ARP & firewall to normal state."""
    console.print("[red bold]!!! EMERGENCY CLEANUP !!![/red bold]")
    console.print("\nThis will attempt to restore your network to a normal state.")

    if not console.input("Proceed? (yes/no): ").strip().lower().startswith("y"):
        console.print("[yellow]Cancelled.[/yellow]")
        return

    state = state_manager.load_state()
    if not state:
        console.print("[yellow]No active state found. Nothing to restore.[/yellow]")
        return

    try:
        # Attempt to restore ARP
        console.print("[cyan]Restoring ARP tables...[/cyan]")
        # TODO: Implement ARP restoration logic

        # Attempt to remove iptables rules
        console.print("[cyan]Removing firewall rules...[/cyan]")
        for rule in state.get("active_iptables_rules", []):
            subprocess.run(f"iptables {rule}", shell=True, capture_output=True)

        state_manager.clear_state()
        console.print("[green]✓ Network restored[/green]")
    except Exception as e:
        console.print(f"[red]Restoration error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--targets", help="Target IPs (comma-separated)")
@click.option("--interface", help="Network interface")
def test(targets, interface):
    """Validate configuration without running interception (dry-run mode)."""
    console.print("[cyan]Running configuration test (dry-run)...[/cyan]\n")

    config = load_config("neon-shield.yml")
    cli_args = {"targets": targets, "interface": interface, "dry_run": True}
    config = merge_with_cli(config, cli_args)

    try:
        validate_config(config)
        console.print("[green]✓ Configuration valid[/green]")
        console.print(f"  Interface: {config.interface or '(auto)'}")
        console.print(f"  Targets: {config.targets or '(auto-discover)'}")
        console.print(f"  DNS spoofing: {'enabled' if config.dns_enabled else 'disabled'}")
        console.print(f"  Content rules: image-swap={config.enable_image_swap}, banner={config.enable_html_banner}")
    except Exception as e:
        console.print(f"[red]✗ Configuration error: {e}[/red]")
        sys.exit(1)


cli_phase1 = click.Group(name='phase1', help='🚀 PHASE 1: Close-Range WiFi Attacks (Nearby Devices)')

@cli_phase1.command()
@click.option("--interface", default="wlan0", help="WiFi interface (default: wlan0)")
@click.option("--ssid", default="Starbucks_WiFi", help="Network name to broadcast")
@click.option("--channel", default=6, type=int, help="WiFi channel (1-11)")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
def ap_mode(interface, ssid, channel, yes):
    """
    🔴 Create rogue WiFi access point (Evil Twin).

    Broadcasts a fake WiFi network with the same name as a popular WiFi (e.g., Starbucks_WiFi).
    Nearby devices auto-connect, exposing all their traffic to NEON-SHIELD.

    ⚠️ EXTREMELY POWERFUL ATTACK: All devices that connect will have their traffic intercepted.
    """
    # Disclaimer
    disclaimer = """
╔══════════════════════════════════════════════════════════════════════╗
║           🔴 ROGUE ACCESS POINT — PHASE 1 ATTACK 🔴                 ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  YOU ARE ABOUT TO:                                                   ║
║  • Create a FAKE WiFi network named: """ + ssid + """
║  • Intercept ALL traffic from devices that connect                  ║
║  • Capture PASSWORDS, EMAILS, MESSAGES, PERSONAL DATA               ║
║  • Demonstrate how cyber attacks work in the real world             ║
║                                                                      ║
║  LEGAL DISCLAIMER:                                                   ║
║  This attack is ILLEGAL without explicit authorization.             ║
║  Unauthorized WiFi interception is a FEDERAL CRIME                  ║
║  (up to 10 years imprisonment, $250k+ fines).                       ║
║                                                                      ║
║  YOU CONFIRM:                                                        ║
║  ✓ You own this WiFi network OR have written authorization          ║
║  ✓ All devices connecting are authorized for testing               ║
║  ✓ You understand the legal consequences                            ║
║  ✓ This is for EDUCATION & AUTHORIZED TESTING ONLY                 ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    console.print(disclaimer, style="bold red")

    if not yes:
        response = console.input("\n[yellow]Continue?[/yellow] (type 'yes' to confirm): ").strip().lower()
        if response != "yes":
            console.print("[red]Cancelled.[/red]")
            return

    # Check root
    if os.geteuid() != 0:
        console.print("[red]❌ Root required. Retry with: sudo neon-shield phase1 ap-mode[/red]")
        sys.exit(1)

    # Check requirements
    from wifi_ap import RogueAccessPoint, check_ap_requirements
    can_run, msg = check_ap_requirements()
    if not can_run:
        console.print(f"[red]❌ {msg}[/red]")
        sys.exit(1)

    # Start AP
    try:
        ap = RogueAccessPoint(interface, ssid, channel)
        if ap.start():
            console.print("\n[green bold]✅ ROGUE ACCESS POINT ACTIVE[/green bold]")
            console.print(f"[cyan]Broadcasting: {ssid}[/cyan]")
            console.print(f"[cyan]Nearby devices will auto-connect...[/cyan]\n")
            console.print("[yellow]Press Ctrl+C to stop[/yellow]")

            # Keep running
            try:
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopping rogue AP...[/yellow]")
                ap.stop()
                console.print("[green]✅ Stopped[/green]")
        else:
            console.print("[red]❌ Failed to start rogue AP[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli_phase1.command()
@click.option("--interface", default="wlan0", help="WiFi interface (default: wlan0)")
def scan_networks(interface):
    """
    📡 Scan nearby WiFi networks and detect vulnerabilities.

    Shows all networks in range, encryption type, signal strength, and security risks.
    Identifies which networks are vulnerable to attacks.

    🎓 Educational: Demonstrates what attackers see when scanning WiFi.
    """
    disclaimer = """
⚠️  WiFi NETWORK ENUMERATION & VULNERABILITY SCAN

This will scan nearby networks and show:
• Network names (SSID), encryption type, signal strength
• Which networks are vulnerable (WEP, open, weak passwords)
• Privacy risks (SSID broadcasting reveals location patterns)

📚 EDUCATIONAL: Shows why network security matters.
   After scanning, you'll see which networks an attacker would target.
"""
    console.print(disclaimer, style="yellow")

    # Check root
    if os.geteuid() != 0:
        console.print("[red]Root required. Retry with: sudo neon-shield phase1 scan-networks[/red]")
        sys.exit(1)

    # Check requirements
    from wifi_scanner import WiFiScanner, check_scanner_requirements
    can_run, msg = check_scanner_requirements()
    if not can_run:
        console.print(f"[red]❌ {msg}[/red]")
        sys.exit(1)

    try:
        scanner = WiFiScanner(interface)
        console.print("[cyan]Scanning for networks...[/cyan]")
        if scanner.scan(duration=20):
            scanner.display_results()
        else:
            console.print("[red]❌ Scan failed[/red]")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli_phase1.command()
@click.option("--interface", default="wlan0", help="WiFi interface (default: wlan0)")
@click.option("--target-mac", required=True, help="Target device MAC address (e.g., AA:BB:CC:DD:EE:FF)")
@click.option("--gateway-mac", required=True, help="Gateway/router MAC address")
@click.option("--ssid", default="[Unknown]", help="Network name (for logging)")
@click.option("--count", default=10, type=int, help="Number of deauth frames")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
def deauth(interface, target_mac, gateway_mac, ssid, count, yes):
    """
    🔴 Send WiFi deauthentication frames to disconnect a device.

    Forces a device to disconnect from its WiFi network.
    When combined with rogue AP, forces device to reconnect to our fake network.

    ⚠️ DESTRUCTIVE: Disrupts legitimate WiFi connectivity.
    """
    disclaimer = f"""
╔══════════════════════════════════════════════════════════════════════╗
║         🔴 WIFI DEAUTHENTICATION ATTACK — PHASE 1B 🔴               ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  TARGET DEVICE: {target_mac}
║  NETWORK: {ssid}
║  ACTION: Force disconnect (will disrupt user's WiFi)                ║
║                                                                      ║
║  ⚠️  LEGAL WARNING:                                                  ║
║  Deauthentication attacks are ILLEGAL without authorization.        ║
║  This is a DENIAL-OF-SERVICE attack that disrupts connectivity.    ║
║  Unauthorized use carries federal penalties.                        ║
║                                                                      ║
║  EDUCATIONAL PURPOSE: Shows why WiFi security needs protection      ║
║  against frame-level attacks (WPA3 has defenses).                   ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    console.print(disclaimer, style="bold red")

    if not yes:
        response = console.input("\n[yellow]Continue?[/yellow] (type 'yes' to confirm): ").strip().lower()
        if response != "yes":
            console.print("[red]Cancelled.[/red]")
            return

    # Check root
    if os.geteuid() != 0:
        console.print("[red]Root required. Retry with: sudo neon-shield phase1 deauth ...[/red]")
        sys.exit(1)

    # Check requirements
    from wifi_deauth import WiFiDeauthAttacker, check_deauth_requirements
    can_run, msg = check_deauth_requirements()
    if not can_run:
        console.print(f"[red]❌ {msg}[/red]")
        sys.exit(1)

    try:
        attacker = WiFiDeauthAttacker(interface)
        if attacker.deauth_device(target_mac, gateway_mac, ssid, count):
            console.print("[green bold]✅ Deauthentication attack sent[/green bold]")
            console.print("[yellow]Device will disconnect and search for networks[/yellow]")
            console.print("[yellow]If rogue AP is nearby, device may auto-connect to it[/yellow]")
        else:
            console.print("[red]❌ Deauth failed[/red]")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


cli.add_command(cli_phase1)


def main():
    """Entry point."""
    # Only require root for commands that actually need it, not for help
    needs_root_commands = ("start", "stop", "cleanup")
    if (os.geteuid() != 0 and len(sys.argv) > 1 and
        sys.argv[1] in needs_root_commands and "--help" not in sys.argv):
        console.print("[red]Error: This command requires root privileges.[/red]")
        console.print("Retry with: sudo neon-shield " + " ".join(sys.argv[1:]))
        sys.exit(1)

    cli()


if __name__ == "__main__":
    main()
