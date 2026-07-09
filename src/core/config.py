"""
Configuration loader for MITM-INTERCEPT.

Loads settings from mitm-intercept.yml, validates, and merges with CLI args
(CLI args override file settings). Provides type-safe access to config values.
"""
import os
import sys
import yaml
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Config:
    """Typed configuration container."""

    # Network
    interface: str = ""
    targets: str = ""
    gateway_ip: str = ""

    # Content Rules
    enable_image_swap: bool = True
    enable_html_banner: bool = True
    banner_text: str = "⚡ MITM-INTERCEPT LAB: traffic intercepted for authorized research."

    # DNS
    dns_enabled: bool = False
    dns_redirects: Dict[str, str] = None

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/mitm-intercept.log"
    max_log_size_mb: int = 100
    log_backup_count: int = 5
    enable_traffic_log: bool = True
    traffic_log_file: str = "logs/traffic.jsonl"
    enable_creds_log: bool = True
    creds_log_file: str = "logs/credentials.jsonl"

    # CA
    certs_dir: str = "certs"
    ca_country: str = "US"
    ca_state: str = "California"
    ca_locality: str = "San Francisco"
    ca_organization: str = "Security Lab"
    ca_common_name: str = "MITM-INTERCEPT Lab CA"

    # Interfaces
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8080
    control_panel_host: str = "127.0.0.1"
    control_panel_port: int = 7070

    # Transparent ports
    http_port: int = 8081
    https_port: int = 8443
    dns_port: int = 5353

    # Health monitoring
    health_monitor_enabled: bool = True
    health_check_interval: int = 10
    health_auto_recover: bool = True
    health_log_checks: bool = False

    # Security
    require_confirmation: bool = True
    audit_log: str = "logs/audit.log"
    api_rate_limit: int = 10

    # Development
    dry_run: bool = False
    verbose: bool = False

    def __post_init__(self):
        if self.dns_redirects is None:
            self.dns_redirects = {}


def load_config(config_path: str = "mitm-intercept.yml") -> Config:
    """
    Load configuration from YAML file.
    If file doesn't exist, returns default Config.
    """
    config = Config()

    if not os.path.exists(config_path):
        print(f"[Config] {config_path} not found, using defaults.")
        return config

    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"[Error] Failed to load config from {config_path}: {e}")
        sys.exit(1)

    # Flatten nested YAML structure into config object
    try:
        if "network" in data:
            net = data["network"]
            config.interface = net.get("interface", "").strip() or ""
            config.targets = net.get("targets", "").strip() or ""
            config.gateway_ip = net.get("gateway_ip", "").strip() or ""

        if "content_rules" in data:
            cr = data["content_rules"]
            config.enable_image_swap = cr.get("enable_image_swap", True)
            config.enable_html_banner = cr.get("enable_html_banner", True)
            config.banner_text = cr.get("banner_text", config.banner_text)

        if "dns_spoofing" in data:
            dns = data["dns_spoofing"]
            config.dns_enabled = dns.get("enabled", False)
            config.dns_redirects = dns.get("redirects", {}) or {}

        if "logging" in data:
            log = data["logging"]
            config.log_level = log.get("level", "INFO").upper()
            config.log_file = log.get("file", config.log_file)
            config.max_log_size_mb = log.get("max_size_mb", 100)
            config.log_backup_count = log.get("backup_count", 5)
            config.enable_traffic_log = log.get("enable_traffic_log", True)
            config.traffic_log_file = log.get("traffic_log_file", config.traffic_log_file)
            config.enable_creds_log = log.get("enable_creds_log", True)
            config.creds_log_file = log.get("creds_log_file", config.creds_log_file)

        if "certificate_authority" in data:
            ca = data["certificate_authority"]
            config.certs_dir = ca.get("certs_dir", "certs")
            if "ca_subject" in ca:
                subj = ca["ca_subject"]
                config.ca_country = subj.get("country", config.ca_country)
                config.ca_state = subj.get("state", config.ca_state)
                config.ca_locality = subj.get("locality", config.ca_locality)
                config.ca_organization = subj.get("organization", config.ca_organization)
                config.ca_common_name = subj.get("common_name", config.ca_common_name)

        if "interfaces" in data:
            ifaces = data["interfaces"]
            if "dashboard" in ifaces:
                dash = ifaces["dashboard"]
                config.dashboard_host = dash.get("host", "0.0.0.0")
                config.dashboard_port = dash.get("port", 8080)
            if "control_panel" in ifaces:
                cp = ifaces["control_panel"]
                config.control_panel_host = cp.get("host", "127.0.0.1")
                config.control_panel_port = cp.get("port", 7070)

        if "transparent" in data:
            trans = data["transparent"]
            config.http_port = trans.get("http_port", 8081)
            config.https_port = trans.get("https_port", 8443)
            config.dns_port = trans.get("dns_port", 5353)

        if "health_monitor" in data:
            hm = data["health_monitor"]
            config.health_monitor_enabled = hm.get("enabled", True)
            config.health_check_interval = hm.get("check_interval", 10)
            config.health_auto_recover = hm.get("auto_recover", True)
            config.health_log_checks = hm.get("log_checks", False)

        if "security" in data:
            sec = data["security"]
            config.require_confirmation = sec.get("require_confirmation", True)
            config.audit_log = sec.get("audit_log", config.audit_log)
            config.api_rate_limit = sec.get("api_rate_limit", 10)

        if "development" in data:
            dev = data["development"]
            config.dry_run = dev.get("dry_run", False)
            config.verbose = dev.get("verbose", False)

        print(f"[Config] Loaded from {config_path}")
        return config

    except Exception as e:
        print(f"[Error] Failed to parse config: {e}")
        sys.exit(1)


def merge_with_cli(config: Config, cli_args: Dict[str, Any]) -> Config:
    """
    Merge CLI arguments into config. CLI args override file settings.
    Only non-None/non-empty CLI args are applied.
    """
    if cli_args.get("interface"):
        config.interface = cli_args["interface"]
    if cli_args.get("targets"):
        config.targets = cli_args["targets"]
    if cli_args.get("dns_redirect"):
        config.dns_enabled = True
        # Parse "domain1:ip1,domain2:ip2" format
        for pair in cli_args["dns_redirect"].split(","):
            if ":" in pair:
                domain, ip = pair.split(":", 1)
                config.dns_redirects[domain.strip()] = ip.strip()
    if cli_args.get("verbose"):
        config.verbose = True
    if cli_args.get("dry_run"):
        config.dry_run = True
    if cli_args.get("yes"):
        config.require_confirmation = False
    if cli_args.get("log_level"):
        config.log_level = cli_args["log_level"].upper()

    return config


def validate_config(config: Config) -> None:
    """Validate config values. Raises SystemExit on error."""
    if config.log_level not in ("DEBUG", "INFO", "WARN", "ERROR"):
        print(f"[Error] Invalid log_level: {config.log_level}")
        sys.exit(1)

    if config.api_rate_limit <= 0:
        print(f"[Error] api_rate_limit must be > 0")
        sys.exit(1)

    if config.health_check_interval <= 0:
        print(f"[Error] health_check_interval must be > 0")
        sys.exit(1)
