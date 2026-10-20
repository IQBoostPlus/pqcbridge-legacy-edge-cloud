# Phase D — Dependency Inventory and Maintenance

Date: 2026-10-20. This record defines maintenance and records the measured lab
runtime; it is not a claim that current dependencies have no vulnerabilities.

## Recorded Inputs

requirements.txt pins cryptography50.0.1 and pytest9.1.1. The offline measured
runtime is Python3.12.14, OpenSSL3.5.7 and cryptography50.0.1; exact installed
packages are in [runtime-packages.json](evidence/runtime-packages.json), with
[runtime metadata](evidence/runtime.json). Python's TLS OpenSSL and cryptography's
bundled OpenSSL are distinct bindings; a Python import alone is not hybrid TLS
validation. Each release records the immutable base/candidate image identities,
source hashes and requirements in its external release.json.

No dependency installation, floating-tag pull or automatic upgrade occurs in the
lab installer. The accepted base is a cached image, not a clean-host download or
a vulnerability audit. The offline image archive supplies reproducible bytes and
has its own digest; an independently trusted release channel remains required.

## Maintenance Procedure

The designated local operator reviews Python/OpenSSL/cryptography upstream
security notices and GitHub advisory/OSV package records before any pilot beyond
this owned simulation, then monthly and on a relevant alert. Record advisory ID,
affected range, runtime binding, reachability and disposition. Use a separate
network-enabled review environment for advisories; do not grant the experiment
external access or install scanning dependencies into its frozen image.

Record unresolved/unavailable advisory queries as unknown. Never infer safety
from a pinned version, a passing test suite or an empty unverified scanner output.
An applicable high-impact unresolved vulnerability blocks broader deployment.
No live advisory audit has been completed by this record.

Evaluate updates in a new immutable image and fresh project. Preserve old image
bytes, data/guard formats and current recovery receipts. Re-run actual TLS floor/
identity rejection, durable fault/recovery checks, management lifecycle, matching
regression and relevant performance/endurance gates. Update pins and runtime
inventory together only after review. An incompatible storage update needs a
separate migration; never edit schema versions or downgrade live state.

Incident ownership and sanitized handover fields are in [OPERATIONS.md](OPERATIONS.md).
