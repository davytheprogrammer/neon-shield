import os
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

class CertificateAuthority:
    def __init__(self, certs_dir="certs"):
        self.certs_dir = os.path.abspath(certs_dir)
        os.makedirs(self.certs_dir, exist_ok=True)
        
        self.ca_key_path = os.path.join(self.certs_dir, "ca.key")
        self.ca_cert_path = os.path.join(self.certs_dir, "ca.crt")
        self.domain_key_path = os.path.join(self.certs_dir, "domain.key")
        
        self.ca_key = None
        self.ca_cert = None
        self.domain_key = None
        
        # In-memory cache of domain certificate paths
        self.cert_cache = {}
        
        self._initialize_ca()
        self._initialize_domain_key()

    def _initialize_ca(self):
        """Loads the Root CA certificate and key, or generates them if they don't exist."""
        if os.path.exists(self.ca_key_path) and os.path.exists(self.ca_cert_path):
            print("[CA] Loading existing Root CA certificate and key...")
            with open(self.ca_key_path, "rb") as f:
                self.ca_key = serialization.load_pem_private_key(f.read(), password=None)
            with open(self.ca_cert_path, "rb") as f:
                self.ca_cert = x509.load_pem_x509_certificate(f.read())
        else:
            print("[CA] Root CA not found. Generating a new Root CA...")
            # Generate Root CA Private Key
            self.ca_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # Serialize CA Key
            with open(self.ca_key_path, "wb") as f:
                f.write(
                    self.ca_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.TraditionalOpenSSL,
                        encryption_algorithm=serialization.NoEncryption()
                    )
                )
                
            # Create CA Subject/Issuer Information
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "EduLab Interception CA"),
                x509.NameAttribute(NameOID.COMMON_NAME, "EduLab Root CA"),
            ])
            
            # Build CA Certificate
            now = datetime.datetime.now(datetime.timezone.utc)
            self.ca_cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                self.ca_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                now - datetime.timedelta(days=1)
            ).not_valid_after(
                now + datetime.timedelta(days=3650) # 10 years validity
            ).add_extension(
                x509.BasicConstraints(ca=True, path_length=None), critical=True
            ).sign(self.ca_key, hashes.SHA256())
            
            # Serialize CA Certificate
            with open(self.ca_cert_path, "wb") as f:
                f.write(self.ca_cert.public_bytes(serialization.Encoding.PEM))
            
            print(f"[CA] New Root CA generated successfully. Saved to: {self.ca_cert_path}")

    def _initialize_domain_key(self):
        """Loads or generates a reusable private key for all domain certificates to optimize performance."""
        if os.path.exists(self.domain_key_path):
            with open(self.domain_key_path, "rb") as f:
                self.domain_key = serialization.load_pem_private_key(f.read(), password=None)
        else:
            print("[CA] Generating a reusable domain private key (optimizing performance)...")
            self.domain_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            with open(self.domain_key_path, "wb") as f:
                f.write(
                    self.domain_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.TraditionalOpenSSL,
                        encryption_algorithm=serialization.NoEncryption()
                    )
                )

    def get_certificate(self, domain):
        """
        Retrieves a certificate for the given domain. If the certificate is not in the
        cache or on disk, it dynamically generates one signed by the Root CA.
        Returns a tuple of (cert_file_path, key_file_path).
        """
        # Clean domain name to handle wildcard matches or ports if passed
        domain = domain.split(":")[0].strip()
        
        # Check in-memory cache first
        if domain in self.cert_cache:
            return self.cert_cache[domain], self.domain_key_path
            
        cert_filename = f"domain_{domain}.crt"
        cert_path = os.path.join(self.certs_dir, cert_filename)
        
        # Check on-disk cache
        if os.path.exists(cert_path):
            self.cert_cache[domain] = cert_path
            return cert_path, self.domain_key_path
            
        # Dynamically generate a certificate signed by our Root CA
        # Subject is the target domain
        subject = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, domain),
        ])
        
        # Subject Alternative Name (SAN) is required by modern browsers
        san = x509.SubjectAlternativeName([x509.DNSName(domain)])
        
        now = datetime.datetime.now(datetime.timezone.utc)
        print(f"[CA] Dynamically generating certificate for domain: {domain}")
        
        # Build Certificate
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            self.ca_cert.subject
        ).public_key(
            self.domain_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            now - datetime.timedelta(days=1)
        ).not_valid_after(
            now + datetime.timedelta(days=365) # 1 year validity
        ).add_extension(
            san, critical=False
        ).sign(self.ca_key, hashes.SHA256())
        
        # Save to disk
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
            
        self.cert_cache[domain] = cert_path
        return cert_path, self.domain_key_path

if __name__ == "__main__":
    # Test the CA initialization and cert generation
    ca = CertificateAuthority()
    cert, key = ca.get_certificate("example.com")
    print(f"Test domain cert paths:\nCert: {cert}\nKey: {key}")
