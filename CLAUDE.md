# CLAUDE.md

This repository contains an **AI-generated baseline** for the course
project "Legacy System Modernization for PQC & LLM-Assisted
Development" (Software Development, Maintenance & Operations).

- The generating prompt is `prompt/P01 - Initial Baseline Generation.md`.
- All code is AI-assisted output awaiting final student review; it
  has been through the P02 review, P04 implementation, P05
  independent verification and P06 remediation, but must NOT be
  presented as secure or production-ready (see README.md §7
  limitations and the `review/P02`–`review/P06` reports).
- Every significant AI interaction must be documented by the student
  team (README.md §9).

## Commands

- Install: `pip install -r requirements.txt`
- Test: `pytest` (from the project root; `pytest.ini` sets the pythonpath)
- Run (3 terminals, in this order):
  1. `python -m cloud.cloud`   (port 5002, health 8002)
  2. `python -m gateway.gateway` (devices 5001, health 8001)
  3. `python -m device.device`
- Docker: `docker compose up --build`

## Architecture

Legacy device (ChaCha20-Poly1305, no ML-KEM) → Edge gateway
(ML-KEM-768 + fallback) → Cloud (ML-KEM-768 decapsulation, in-memory
store). Plain TCP, JSON-lines protocol, no TLS. See README.md for
details and known limitations.
