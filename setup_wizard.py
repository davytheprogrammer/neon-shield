"""
Interactive setup wizard for MITM-INTERCEPT.

Guides users through first-time configuration.
"""
import os
import sys
from typing import List, Tuple

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
except ImportError:
    # Fallback if rich not installed
    class Console:
        def print(self, *args, **kwargs):
            print(*args)

    class Panel:
        def __init__(self, *args, **kwargs):
            pass

    class Prompt:
        @staticmethod
        def ask(prompt, default=None):
            return input(f"{prompt} [{default}]: ").strip() or default

    class Confirm:
        @staticmethod
        def ask(prompt, default=False):
            return input(f"{prompt} (y/n) [{default}]: ").lower().startswith('y')

console = Console()


DISCLAIMER = """
⚠️  MITM-INTERCEPT EDUCATIONAL USE DISCLAIMER ⚠️

MITM-INTERCEPT performs ACTIVE MITM ATTACKS on local networks:
• ARP spoofing to intercept traffic from other devices
• TLS decryption to read HTTPS traffic
• Credential capture, DNS spoofing, content injection

These attacks are FEDERAL CRIMES without explicit authorization.

YOU CONFIRM:
✓ Every device you target is owned by you OR you have explicit written
  authorization from the owner/operator (e.g., a signed pentest agreement).
✓ This network is yours OR you're authorized to test it.
✓ You understand this tool is for EDUCATION & AUTHORIZED RESEARCH only.
✓ You understand the legal consequences: felony charges, fines, imprisonment.

If you're unsure whether you're authorized, DO NOT PROCEED.
"""


def show_disclaimer() -> bool:
    """Show disclaimer and ask for confirmation."""
    console.print(Panel(DISCLAIMER, title="⚡ LEGAL DISCLAIMER", border_style="red"))
    return Confirm.ask("I confirm I am authorized to use this tool on this network", default=False)


def ask_network_config() -> Tuple[str, str]:
    """Ask for network interface and target devices."""
    console.print("\n[1/4] Network Configuration\n")

    interface = Prompt.ask("Network interface (leave blank to auto-detect)", default="")
    if interface:
        interface = interface.strip()

    targets = Prompt.ask(
        "Target device IPs (comma-separated, or blank to auto-discover)",
        default="",
    )
    if targets:
        targets = targets.strip()

    return interface, targets


def ask_content_rules() -> Tuple[bool, bool]:
    """Ask which content rules to enable."""
    console.print("\n[2/4] Content Manipulation Rules\n")

    enable_images = Confirm.ask("Replace images with lab logo (image-swap)", default=True)
    enable_banner = Confirm.ask("Inject HTML banner on web pages", default=True)

    return enable_images, enable_banner


def ask_dns_spoofing() -> Tuple[bool, str]:
    """Ask about DNS spoofing."""
    console.print("\n[3/4] DNS Spoofing (Optional)\n")

    enable = Confirm.ask("Enable DNS spoofing for specific domains", default=False)
    if not enable:
        return False, ""

    console.print(
        "\nEnter domain:IP mappings (comma-separated).\n"
        "Example: example.com:192.168.1.1, test.com:192.168.1.1\n"
    )
    redirects = Prompt.ask("DNS redirects (or blank to skip)", default="")

    return True, redirects.strip() if redirects else ""


def ask_logging() -> Tuple[str, bool, bool]:
    """Ask about logging preferences."""
    console.print("\n[4/4] Logging & Monitoring\n")

    log_level = Prompt.ask(
        "Log level (DEBUG, INFO, WARN, ERROR)",
        default="INFO",
    ).upper()
    if log_level not in ("DEBUG", "INFO", "WARN", "ERROR"):
        log_level = "INFO"

    enable_traffic_log = Confirm.ask("Log all intercepted traffic", default=True)
    enable_creds_log = Confirm.ask("Log captured credentials", default=True)

    return log_level, enable_traffic_log, enable_creds_log


def run_wizard() -> dict:
    """Run the full interactive setup wizard."""
    console.print(Panel("Welcome to MITM-INTERCEPT Setup", style="bold cyan"))

    # Disclaimer
    if not show_disclaimer():
        console.print("[red]Setup cancelled. Authorization not confirmed.[/red]")
        sys.exit(1)

    # Network
    interface, targets = ask_network_config()

    # Content rules
    enable_images, enable_banner = ask_content_rules()

    # DNS spoofing
    dns_enabled, dns_redirects = ask_dns_spoofing()

    # Logging
    log_level, enable_traffic_log, enable_creds_log = ask_logging()

    config = {
        "network": {
            "interface": interface,
            "targets": targets,
        },
        "content_rules": {
            "enable_image_swap": enable_images,
            "enable_html_banner": enable_banner,
        },
        "dns_spoofing": {
            "enabled": dns_enabled,
            "redirects_str": dns_redirects,
        },
        "logging": {
            "level": log_level,
            "enable_traffic_log": enable_traffic_log,
            "enable_creds_log": enable_creds_log,
        },
    }

    console.print("\n[green]✓ Setup complete![/green]")
    console.print("Starting MITM-INTERCEPT...\n")

    return config
