"""Offline synthetic lab issuer. Private material is written only to fresh directories."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import sys

from cryptography import x509
from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


class CredentialError(ValueError):
    """A safe fixed-code credential operation refusal."""


_ROOT = Path(__file__).resolve().parents[1]
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")


def _external(directory):
    path = Path(directory)
    if not path.is_absolute():
        raise CredentialError("absolute_directory_required")
    resolved = path.resolve()
    if resolved == _ROOT or _ROOT in resolved.parents:
        raise CredentialError("external_directory_required")
    return resolved


def _fresh(directory):
    path = _external(directory)
    try:
        path.mkdir(mode=0o700)
    except OSError:
        raise CredentialError("fresh_directory_required") from None
    return path


def _now(value=None):
    value = datetime.now(timezone.utc) if value is None else value
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise CredentialError("aware_utc_time_required")
    return value.astimezone(timezone.utc).replace(microsecond=0)


def _write(path, body):
    # Exclusive creation and mode at creation avoid a permissive private-key window.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())


def _save(directory, key, cert):
    key_file, cert_file = directory / "key.pem", directory / "cert.pem"
    try:
        _write(key_file, key.private_bytes(serialization.Encoding.PEM,
               serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        _write(cert_file, cert.public_bytes(serialization.Encoding.PEM))
    except OSError:
        # Retain a partial fresh directory for explicit operator inspection; never overwrite.
        raise CredentialError("credential_write_failed") from None
    return {"fingerprint": cert.fingerprint(hashes.SHA256()).hex(),
            "cert_file": str(cert_file), "key_file": str(key_file),
            "not_before": cert.not_valid_before_utc.isoformat(),
            "not_after": cert.not_valid_after_utc.isoformat()}


def create_issuer(directory, common_name="PQC lab issuer"):
    """Create a fresh seven-day synthetic RSA CA; return public metadata/references."""
    if not isinstance(common_name, str) or not 1 <= len(common_name) <= 64 or any(ord(c) < 32 or ord(c) > 126 for c in common_name) or not common_name.strip():
        raise CredentialError("invalid_issuer_name")
    directory = _fresh(directory)
    now = _now()
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now).not_valid_after(now + timedelta(days=7))
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
            .add_extension(x509.KeyUsage(digital_signature=True, content_commitment=False,
                key_encipherment=False, data_encipherment=False, key_agreement=False,
                key_cert_sign=True, crl_sign=True, encipher_only=False, decipher_only=False), critical=True)
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
            .sign(key, hashes.SHA256()))
    return _save(directory, key, cert)


def issue_certificate(issuer_dir, output_dir, role, subject_id, *, hostname="cloud",
                      lifetime_seconds=86400, now=None):
    """Issue one <=24-hour synthetic role leaf in a fresh external directory."""
    if role not in ("gateway", "cloud"):
        raise CredentialError("invalid_role")
    if not isinstance(subject_id, str) or not _ID.fullmatch(subject_id):
        raise CredentialError("invalid_subject_id")
    if not isinstance(hostname, str) or len(hostname) > 253 or not all(
            re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
            for label in hostname.split(".")):
        raise CredentialError("invalid_hostname")
    if type(lifetime_seconds) is not int or not 1 <= lifetime_seconds <= 86400:
        raise CredentialError("invalid_lifetime")
    at = _now(now)
    issuer_dir = _external(issuer_dir)
    try:
        with (issuer_dir / "cert.pem").open("rb") as stream:
            cert_bytes = stream.read(32769)
        with (issuer_dir / "key.pem").open("rb") as stream:
            key_bytes = stream.read(32769)
        if len(cert_bytes) > 32768 or len(key_bytes) > 32768:
            raise ValueError()
        ca = x509.load_pem_x509_certificate(cert_bytes)
        ca_key = serialization.load_pem_private_key(key_bytes, None)
        ca_public_key = ca.public_key()
        if (not isinstance(ca_key, rsa.RSAPrivateKey) or ca_key.key_size < 2048
                or not isinstance(ca_public_key, rsa.RSAPublicKey)):
            raise ValueError()
        if ca_key.public_key().public_numbers() != ca_public_key.public_numbers():
            raise ValueError()
        if not ca.extensions.get_extension_for_class(x509.BasicConstraints).value.ca or not ca.extensions.get_extension_for_class(x509.KeyUsage).value.key_cert_sign:
            raise ValueError()
        if at < ca.not_valid_before_utc or at + timedelta(seconds=lifetime_seconds) > ca.not_valid_after_utc:
            raise ValueError()
        ca.verify_directly_issued_by(ca)
    except (OSError, ValueError, TypeError, OverflowError, InvalidSignature,
            UnsupportedAlgorithm, x509.ExtensionNotFound):
        raise CredentialError("invalid_or_expired_issuer") from None
    directory = _fresh(output_dir)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    builder = (x509.CertificateBuilder()
               .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject_id)]))
               .issuer_name(ca.subject).public_key(key.public_key())
               .serial_number(x509.random_serial_number()).not_valid_before(at)
               .not_valid_after(at + timedelta(seconds=lifetime_seconds))
               .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
               .add_extension(x509.KeyUsage(digital_signature=True, content_commitment=False,
                    key_encipherment=False, data_encipherment=False, key_agreement=False,
                    key_cert_sign=False, crl_sign=False, encipher_only=False, decipher_only=False), critical=True)
               .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH if role == "cloud" else ExtendedKeyUsageOID.CLIENT_AUTH]), critical=False)
               .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca.public_key()), critical=False))
    if role == "cloud":
        builder = builder.add_extension(x509.SubjectAlternativeName([x509.DNSName(hostname)]), critical=False)
    result = _save(directory, key, builder.sign(ca_key, hashes.SHA256()))
    return dict(result, role=role, subject_id=subject_id, revoked=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    issuer = commands.add_parser("issuer")
    issuer.add_argument("--directory", required=True)
    issuer.add_argument("--common-name", default="PQC lab issuer")
    issue = commands.add_parser("issue")
    issue.add_argument("--issuer-dir", required=True)
    issue.add_argument("--output-dir", required=True)
    issue.add_argument("--role", choices=("gateway", "cloud"), required=True)
    issue.add_argument("--subject-id", required=True)
    issue.add_argument("--hostname", default="cloud")
    issue.add_argument("--lifetime-seconds", type=int, default=86400)
    args = parser.parse_args(argv)
    try:
        if args.command == "issuer":
            result = create_issuer(args.directory, args.common_name)
        else:
            result = issue_certificate(args.issuer_dir, args.output_dir, args.role,
                args.subject_id, hostname=args.hostname, lifetime_seconds=args.lifetime_seconds)
    except CredentialError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
