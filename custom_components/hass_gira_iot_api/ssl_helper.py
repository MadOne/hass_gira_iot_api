"""SSL certificate helper utilities.

This module provides a helper to generate a self-signed X.509 certificate
for development and testing purposes only.

Notes:
-----
- The generated certificate is intended for local development and testing.
  Do not use these certificates in production environments.
- The implementation is a slightly modified version of a public gist and
  retains the original license (MIT). See header comments for details.
"""

# This is a slightly modified version from https://gist.github.com/bloodearnest/9017111a313777b9cce5

# Original license

# Copyright 2018 Simon Davy
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# WARNING: the code in the gist generates self-signed certs, for the purposes of testing in development.
# Do not use these certs in production, or You Will Have A Bad Time.
#
# Caveat emptor
#

from datetime import UTC, datetime, timedelta
import ipaddress

from aiofiles import open as aiofiles_open
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


async def generate_selfsigned_cert(hostname, ip_addresses=None, key=None):
    """Generate a self-signed certificate and private key files.

    The function creates a self-signed X.509 certificate and a matching
    private key, writes them to `domain_srv.crt` and `domain_srv.key` in the
    current working directory, and returns nothing.

    Parameters
    ----------
    hostname : str
        The common name (CN) and DNS SubjectAlternativeName to include in the
        certificate.
    ip_addresses : list[str] | None, optional
        Optional list of IP address strings to include in the SAN. Each entry
        will be added both as a DNSName (for OpenSSL compatibility) and as an
        IPAddress (for stricter TLS implementations) where appropriate.
    key : rsa.RSAPrivateKey | None, optional
        Optional existing RSA private key to use. If not provided, a new 2048
        bit RSA key will be generated.

    Returns:
    -------
    None

    Warnings:
    --------
    - The generated certificate is long-lived (10 years by default) and is
      suitable only for testing. Do not use it in production.
    - The function writes files to the current working directory without
      additional safeguards.
    """
    # Generate our key
    if key is None:
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        )

    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, hostname)])

    # best practice seem to be to include the hostname in the SAN, which *SHOULD* mean COMMON_NAME is ignored.
    alt_names = [x509.DNSName(hostname)]

    # allow addressing by IP, for when you don't have real DNS (common in most testing scenarios
    if ip_addresses:
        for addr in ip_addresses:
            # openssl wants DNSnames for ips...
            alt_names.append(x509.DNSName(addr))
            # ... whereas golang's crypto/tls is stricter, and needs IPAddresses
            # note: older versions of cryptography do not understand ip_address objects
            alt_names.append(x509.IPAddress(ipaddress.ip_address(addr)))

    san = x509.SubjectAlternativeName(alt_names)

    # path_len=0 means this cert can only sign itself, not other certs.
    basic_contraints = x509.BasicConstraints(ca=True, path_length=0)
    now = datetime.now(tz=UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(1000)
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=10 * 365))
        .add_extension(basic_contraints, False)
        .add_extension(san, False)
        .sign(key, hashes.SHA256(), default_backend())
    )
    cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM)
    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # works, besides bytes instead of string warnings
    async with aiofiles_open("domain_srv.crt", "wb") as f:
        await f.write(cert_pem)
    async with aiofiles_open("domain_srv.key", "wb") as f:
        await f.write(key_pem)
