#!/usr/bin/env python3
"""One-time Docker trust-anchor provisioning for the edge-cloud demo.

First start after a fresh clone (and again whenever the cloud_state
volume is recreated, e.g. after `docker compose down -v`):

    python scripts/docker_bootstrap.py

Steps (plain `docker compose`, Python standard library only):
  1. start ONLY the cloud service and wait for its /health endpoint.
     On first start the cloud generates its ML-KEM-768 keypair and
     persists it in the cloud_state volume (F-01 trust anchor).
  2. read the cloud's ML-KEM public key SHA-256 fingerprint from the
     cloud container logs (public material - safe to store; the
     private key never leaves the container).
  3. write CLOUD_PUBLIC_KEY_SHA256=<fingerprint> to .env (gitignored;
     this is the pin the gateway verifies against).
  4. start the remaining services (gateway + device).
  5. wait until the cloud logs an established ML-KEM-768 session and
     has stored at least one device reading.

The gateway FAILS CLOSED whenever the pin is missing or wrong, so
step 3 is the trust-anchor provisioning step this script automates.

Re-running the script is safe: the cloud loads its persisted keypair
from the cloud_state volume and the same fingerprint is provisioned
again.
"""
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = REPO_ROOT / ".env"
CLOUD_HEALTH_URL = "http://127.0.0.1:8002/health"
FINGERPRINT_RE = re.compile(r"[0-9a-f]{64}")
HEALTH_TIMEOUT_S = 180.0
VERIFY_TIMEOUT_S = 90.0
POLL_INTERVAL_S = 2.0


def run_compose(args):
    print("+ docker compose " + " ".join(args), flush=True)
    subprocess.run(["docker", "compose", *args], cwd=REPO_ROOT, check=True)


def compose_logs(service):
    result = subprocess.run(
        ["docker", "compose", "logs", service],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    return result.stdout


def cloud_health_ok():
    try:
        with urllib.request.urlopen(CLOUD_HEALTH_URL, timeout=2) as response:
            return response.status == 200
    except OSError:
        return False


def cloud_readings_count():
    try:
        with urllib.request.urlopen(CLOUD_HEALTH_URL, timeout=2) as response:
            body = json.loads(response.read().decode("utf-8"))
            return int(body.get("stored_readings", 0))
    except (OSError, ValueError):
        return 0


def wait_until(condition, timeout_s, description):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if condition():
            print("OK: " + description, flush=True)
            return
        time.sleep(POLL_INTERVAL_S)
    sys.exit("FAILED: timed out waiting for " + description + ".\n"
             "  Inspect the services with: docker compose ps && "
             "docker compose logs")


def extract_fingerprint(logs):
    """The cloud prints a label line, then the fingerprint on its own
    line. Anchor to the LAST occurrence so that a recreated keypair
    (wiped volume, recreated container) yields the CURRENT one."""
    label = "ML-KEM public key SHA-256 fingerprint"
    match = FINGERPRINT_RE.search(logs.rsplit(label, 1)[-1])
    if match is None:
        sys.exit("FAILED: no ML-KEM public key fingerprint found in "
                 "`docker compose logs cloud`")
    return match.group(0)


def main():
    run_compose(["up", "-d", "cloud"])
    wait_until(cloud_health_ok, HEALTH_TIMEOUT_S, "the cloud /health endpoint")
    fingerprint = extract_fingerprint(compose_logs("cloud"))
    print("cloud ML-KEM public key SHA-256 fingerprint: " + fingerprint,
          flush=True)
    ENV_FILE.write_text(
        "CLOUD_PUBLIC_KEY_SHA256=" + fingerprint + "\n", encoding="utf-8")
    print("provisioned " + ENV_FILE.name + ": CLOUD_PUBLIC_KEY_SHA256="
          + fingerprint, flush=True)
    run_compose(["up", "-d"])
    wait_until(lambda: "ML-KEM-768 session" in compose_logs("cloud"),
               VERIFY_TIMEOUT_S,
               "an established ML-KEM-768 gateway session (cloud logs)")
    wait_until(lambda: cloud_readings_count() >= 1, VERIFY_TIMEOUT_S,
               "at least one device reading stored by the cloud")
    print("bootstrap complete: the device -> gateway -> cloud pipeline "
          "is running with the provisioned pin.", flush=True)


if __name__ == "__main__":
    main()
