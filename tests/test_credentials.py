"""Synthetic issuer public filesystem/API and CLI boundaries."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import os
import stat
import subprocess
import sys

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, padding
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
import pytest


def test_issuer_and_role_leaves_are_verifiable_and_key_matched(tmp_path):
    from common.credentials import create_issuer, issue_certificate
    issuer = create_issuer(tmp_path / "issuer")
    ca = x509.load_pem_x509_certificate(Path(issuer["cert_file"]).read_bytes())
    assert ca.extensions.get_extension_for_class(x509.BasicConstraints).critical
    assert ca.extensions.get_extension_for_class(x509.BasicConstraints).value.ca
    for role, identity, eku in (("gateway", "gw-lab", ExtendedKeyUsageOID.CLIENT_AUTH),
                                ("cloud", "cloud-lab", ExtendedKeyUsageOID.SERVER_AUTH)):
        descriptor = issue_certificate(tmp_path / "issuer", tmp_path / role, role, identity)
        cert = x509.load_pem_x509_certificate(Path(descriptor["cert_file"]).read_bytes())
        key = serialization.load_pem_private_key(Path(descriptor["key_file"]).read_bytes(), None)
        ca.public_key().verify(cert.signature, cert.tbs_certificate_bytes,
                               padding.PKCS1v15(), cert.signature_hash_algorithm)
        assert cert.public_key().public_numbers() == key.public_key().public_numbers()
        assert cert.fingerprint(hashes.SHA256()).hex() == descriptor["fingerprint"]
        assert cert.not_valid_after_utc - cert.not_valid_before_utc <= timedelta(hours=24)
        assert list(cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value) == [eku]
        assert cert.extensions.get_extension_for_class(x509.BasicConstraints).value.ca is False
        assert descriptor["role"] == role and descriptor["subject_id"] == identity
        assert descriptor["revoked"] is False
        assert "PRIVATE KEY" not in str(descriptor)
        if role == "cloud":
            assert cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(x509.DNSName) == ["cloud"]


def test_corrupt_issuer_signature_is_refused_without_creating_leaf(tmp_path):
    from common.credentials import CredentialError, create_issuer, issue_certificate
    descriptor = create_issuer(tmp_path / "issuer")
    cert_path = Path(descriptor["cert_file"])
    cert = x509.load_pem_x509_certificate(cert_path.read_bytes())
    raw = bytearray(cert.public_bytes(serialization.Encoding.DER))
    raw[-1] ^= 1
    corrupt = x509.load_der_x509_certificate(bytes(raw))
    cert_path.write_bytes(corrupt.public_bytes(serialization.Encoding.PEM))
    with pytest.raises(CredentialError, match="invalid_or_expired_issuer"):
        issue_certificate(tmp_path / "issuer", tmp_path / "leaf", "gateway", "gw-lab")
    assert not (tmp_path / "leaf").exists()


def test_unsupported_issuer_public_key_has_fixed_refusal(tmp_path):
    from common.credentials import CredentialError, create_issuer, issue_certificate
    descriptor = create_issuer(tmp_path / "issuer")
    alternate_key = ed25519.Ed25519PrivateKey.generate()
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "alternate issuer")])
    now = datetime.now(timezone.utc)
    alternate = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
                 .public_key(alternate_key.public_key()).serial_number(x509.random_serial_number())
                 .not_valid_before(now).not_valid_after(now + timedelta(days=2))
                 .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
                 .sign(alternate_key, None))
    Path(descriptor["cert_file"]).write_bytes(alternate.public_bytes(serialization.Encoding.PEM))
    with pytest.raises(CredentialError, match="^invalid_or_expired_issuer$"):
        issue_certificate(tmp_path / "issuer", tmp_path / "leaf", "gateway", "gw-lab")
    assert not (tmp_path / "leaf").exists()


def test_fresh_directories_never_overwrite_existing_private_material(tmp_path):
    from common.credentials import CredentialError, create_issuer, issue_certificate
    descriptor = create_issuer(tmp_path / "issuer")
    original = Path(descriptor["key_file"]).read_bytes()
    with pytest.raises(CredentialError, match="fresh_directory_required"):
        create_issuer(tmp_path / "issuer")
    assert Path(descriptor["key_file"]).read_bytes() == original
    leaf = issue_certificate(tmp_path / "issuer", tmp_path / "leaf", "gateway", "gw-lab")
    original_leaf = Path(leaf["key_file"]).read_bytes()
    with pytest.raises(CredentialError, match="fresh_directory_required"):
        issue_certificate(tmp_path / "issuer", tmp_path / "leaf", "gateway", "gw-lab")
    assert Path(leaf["key_file"]).read_bytes() == original_leaf
    if os.name != "nt":
        assert stat.S_IMODE((tmp_path / "issuer").stat().st_mode) == 0o700
        assert stat.S_IMODE((tmp_path / "leaf").stat().st_mode) == 0o700
        assert stat.S_IMODE(Path(leaf["key_file"]).stat().st_mode) == 0o600
        assert stat.S_IMODE(Path(descriptor["key_file"]).stat().st_mode) == 0o600


@pytest.mark.parametrize("change", [
    {"role": "server"}, {"subject_id": "../escape"}, {"subject_id": ""},
    {"subject_id": "x\nsecret"}, {"hostname": "*.cloud"},
    {"hostname": "cloud/escape"}, {"hostname": "cloud..lab"},
    {"hostname": "-cloud"}, {"hostname": "cloud-"},
    {"lifetime_seconds": 0}, {"lifetime_seconds": 86401},
    {"lifetime_seconds": True}, {"lifetime_seconds": 1.5},
    {"now": datetime(2026, 1, 1)},
])
def test_invalid_requests_do_not_create_output_or_expose_input(tmp_path, change):
    from common.credentials import CredentialError, create_issuer, issue_certificate
    create_issuer(tmp_path / "issuer")
    args = dict(role="gateway", subject_id="gw-lab")
    args.update(change)
    with pytest.raises(CredentialError):
        issue_certificate(tmp_path / "issuer", tmp_path / "leaf", **args)
    assert not (tmp_path / "leaf").exists()


def test_relative_checkout_and_issuer_expiry_boundaries(tmp_path):
    from common.credentials import CredentialError, create_issuer, issue_certificate
    with pytest.raises(CredentialError, match="absolute_directory_required"):
        create_issuer(Path("relative"))
    with pytest.raises(CredentialError, match="external_directory_required"):
        create_issuer(Path(__file__).resolve().parents[1] / "tmp" / "should-not-exist")
    issuer = create_issuer(tmp_path / "issuer")
    after = datetime.fromisoformat(issuer["not_after"])
    with pytest.raises(CredentialError, match="invalid_or_expired_issuer"):
        issue_certificate(tmp_path / "issuer", tmp_path / "leaf", "gateway", "gw-lab", now=after)
    assert not (tmp_path / "leaf").exists()
    with pytest.raises(CredentialError, match="invalid_or_expired_issuer"):
        issue_certificate(tmp_path / "issuer", tmp_path / "leaf", "gateway", "gw-lab", now=datetime(9999, 12, 31, tzinfo=timezone.utc))


def test_issuer_cli_emits_public_descriptor_and_fixed_error_only(tmp_path):
    root = Path(__file__).resolve().parents[1]
    issuer = tmp_path / "cli-issuer"
    created = subprocess.run([sys.executable, "-B", "-m", "common.credentials", "issuer",
                              "--directory", str(issuer)], cwd=root, text=True,
                             capture_output=True, timeout=10)
    assert created.returncode == 0, created.stderr
    public = json.loads(created.stdout)
    assert Path(public["cert_file"]).is_file() and Path(public["key_file"]).is_file()
    issued = subprocess.run([sys.executable, "-B", "-m", "common.credentials", "issue",
        "--issuer-dir", str(issuer), "--output-dir", str(tmp_path / "cli-cloud"),
        "--role", "cloud", "--subject-id", "cloud-lab", "--lifetime-seconds", "60"],
        cwd=root, text=True, capture_output=True, timeout=10)
    assert issued.returncode == 0, issued.stderr
    leaf = json.loads(issued.stdout)
    assert leaf["role"] == "cloud" and leaf["revoked"] is False
    assert "PRIVATE KEY" not in created.stdout + issued.stdout + created.stderr + issued.stderr
    duplicate = subprocess.run([sys.executable, "-B", "-m", "common.credentials", "issuer",
                                "--directory", str(issuer)], cwd=root, text=True,
                               capture_output=True, timeout=10)
    assert duplicate.returncode == 2 and duplicate.stdout == ""
    assert duplicate.stderr.strip() == "fresh_directory_required"
