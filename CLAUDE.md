# CLAUDE.md

PQC Bridge is an engineering prototype for verifiable post-quantum migration of
legacy edge-to-cloud telemetry. Initial development history is in
`docs/development/initial/README.md`; current engineering evidence is in
`docs/phase-a/` and `docs/phase-b/`. Consult `PROJECT_STATE.md` for local recovery
and pause instructions before implementation.

Phase A/B acceptance is limited to the owned Docker/simulated-device lab. Do not
claim physical-device compatibility or production security from these results.
The commands below describe the initial V1 path; the opt-in engineering path is
documented in `docs/phase-b/OPERATIONS.md`.

## Documentation and Publication

Write all project documentation in English. Communicate with the user in Chinese.
For new or revised development records, follow `docs/development/README.md` and
`docs/development/RECORD_TEMPLATE.md`, using the initial P01–P08 records as the
evidence-first style reference. Preserve historical findings and review status.

When GitHub publication is authorized, commit the intended changes and push
directly to the intended branch. Do not create a pull request unless the user
explicitly changes this preference. Use ordinary non-forced pushes and verify
the remote commit. This preference does not authorize unrelated or incomplete
work to be published automatically.

## Commands

- Install: `pip install -r requirements.txt`
- Test: `pytest` (from the project root; `pytest.ini` sets the pythonpath;
  136 passed at the end of P08)
- Run (3 terminals, in this order):
  1. `python -m cloud.cloud`   (port 5002, health 8002)
  2. `python -m gateway.gateway` (devices 5001, health 8001)
  3. `python -m device.device`
- Docker: `docker compose up --build`

Gateway-to-cloud authentication (P08 BF-01) and config-driven
credentials (P08 BF-03A) are enabled by default using the committed
`common/demo_*_keys.json` demo material; supply real keys via
`GATEWAY_KEYS_FILE` / `GATEWAY_KEYS_JSON`, `GATEWAY_KEY_HEX`,
`DEVICE_KEYS_FILE` / `DEVICE_KEYS_JSON` and `DEVICE_KEY_HEX`.

## Initial V1 Architecture

Legacy device (ChaCha20-Poly1305, no ML-KEM) → Edge gateway
(ML-KEM-768 + fallback) → Cloud (ML-KEM-768 decapsulation, in-memory
store). Plain TCP, JSON-lines protocol, no TLS. See README.md for
details and known limitations.
