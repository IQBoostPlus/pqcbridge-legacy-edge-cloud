# Phase D — Synthetic Pilot Operations

Date: 2026-10-20. In-progress package; consult [STATUS.md](STATUS.md) before use.
Scope: one owned Docker Desktop Linux/amd64 project, simulated source only.
No physical device, public endpoint or production mode. V1 stays separate.

## 1. Install and Establish Trust

Use Python 3.12 and the native Docker CLI with the local desktop-linux context.
The runtime directory must be new, absolute and outside the checkout. The
controller accepts only the recorded immutable A/B base image. No image pull or
dependency installation occurs during an offline build. A missing base is a
blocker; obtain the approved image archive through the trusted release channel.

```powershell
$pilot = 'D:\Code\pqcbridge-phase-d-artifacts\my-new-pilot'
$docker = 'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
python scripts/phase_d/package.py init --root $pilot --docker-cli $docker
python "$pilot\package.observed.py" start --root $pilot --docker-cli $docker
python "$pilot\package.observed.py" status --root $pilot --docker-cli $docker
```

Initialization generates a new offline synthetic issuer, role-isolated leaves,
source key/incarnation and independent health token. Trust comes from the local
provisioning artifact public-trust.json and its sealed hash in release.json,
never from service logs. Copy/verify that public artifact via the trusted local
administrator before distributing credentials. The manifest is a consistency
record, not a signed supply-chain attestation. Demo source keys are refused.
The CLI refuses scope values other than simulation; it cannot authorize a real
deployment. Never import existing V1 state or paste real secrets into examples.

The exported controller works from the bundle with source/common and does not
need the original checkout. release.json records source SHA-256 values, exact
image identity, package revision, Compose hash and pinned dependencies. For
offline transport, export the validated base and candidate images:

```powershell
python "$pilot\package.observed.py" export --root $pilot --docker-cli $docker
# On the intended trusted host, verify the independently supplied release record:
python "$pilot\package.observed.py" import --root $pilot --docker-cli $docker
```

The image archive has its own checksum. A new independent installation should
then run init with a fresh root, generating new secrets and namespaces. Carry
source plus controller and image archive; a checksum alone cannot supply bytes.
Bare-host installation is not implied by a fresh-project lab result.

## 2. Limits, Lease Renewal and Credentials

Services have read-only roots, dropped capabilities, no-new-privileges, internal
networking and no published host ports. Linux named state volumes keep SQLite
WAL/FULL durability off Windows bind storage. CPU/memory/PID budgets are 0.5 CPU,
256 MiB and64; logs rotate at two8MiB files. Health stays on service loopback.
The offline admin alone mounts issuer/private recovery material and both state
volumes. There is no Docker socket mount or online management API.

Fresh Windows bundle/vault directories receive explicit current-user, SYSTEM and
Administrators access without inherited grants; existing user directories are
not changed. Linux state/private keys retain0700/0600 settings. Windows access
control and Linux mode observations must be reported separately. This does not
protect against a compromised host or administrator. Backups contain private
keys, source keys, health tokens and sensor state: keep them in a restricted,
encrypted offline store; never Git, logs or ordinary support attachments.

Renew the maximum300-second manifest lease before expiry. This is an explicit
operator action, not an unconditional service fallback:

```powershell
python "$pilot\package.observed.py" renew --root $pilot --docker-cli $docker
python "$pilot\package.observed.py" rotate --root $pilot --docker-cli $docker
```

Rotation issues both role leaves, advances the configuration version and revokes
their old leaves without changing source/event identities. Verify a new live
matching business ACK afterward; a successful CLI command is not proof of
Effective delivery. The bounded issuer/credential catalog is not an unlimited
renewal service. The human-amended 30-minute supervisor rotates every450s and
renews every150s, requiring at least three actual both-role rotations;
this stays below the C limits of12 credentials/1,000 audit actions for one run.
Failure stops the experiment; extending credential lifetime is not a remedy.

## 3. Cold Backup and Isolated Restore

Stop both services and freeze source admission. The controller verifies both
owned containers are stopped before copying the full coordinated cohort:
delivery databases, source sequences, cloud deduplication, catalog/audit,
anti-rollback guards, manifest, trust/configuration, role credentials and offline
issuer/issued material. SQLite checkpointing and integrity/schema checks precede
the inventory. File hashing streams bounded chunks. Do not back up only a DB
while discarding its matching revocation/source state.

```powershell
python "$pilot\package.observed.py" stop --root $pilot --docker-cli $docker
$vault = 'D:\Code\pqcbridge-phase-d-artifacts\my-new-private-vault'
python "$pilot\package.observed.py" backup --root $pilot --checkpoint-root $vault --docker-cli $docker
```

Keep the returned current manifest_sha256 receipt independently of the vault.
When an incident leaves the latest receipt unknown, recovery is blocked: an old
receipt plus an old backup is not evidence that no newer messages/revocations
existed. This design trusts the local recovery authority; it is not a remote
monotonic counter or host-compromise defense. Never reuse an older receipt to
make a restore succeed. Preserve the surviving current state for reconciliation.

Restore only into a new isolated package/project with empty role volumes:

```powershell
$restored = 'D:\Code\pqcbridge-phase-d-artifacts\my-new-restored-pilot'
$receipt = '<independently-retained-current-manifest-sha256>'
python scripts/phase_d/package.py restore --root $restored --checkpoint-root $vault --expected-digest $receipt --package-version pilot-lab-v1.1 --docker-cli $docker
python "$restored\package.observed.py" start --root $restored --docker-cli $docker
```

Wrong receipts, altered contents, unsupported schemas and nonempty destinations
are refused. Validate accepted/ACK/committed counts, exact business IDs/digest,
source checkpoint, live ACK, fresh credential rotation and guard state before
using the recovered project. Keep the original stopped/fenced. Never run two
copies as one site or clear guards to bypass a refusal. Lost host writes after
the last coordinated checkpoint cannot be invented by recovery; an unreconciled
gap blocks promotion. No filesystem power-loss or general hot-backup claim.

## 4. Same-Schema Upgrade and Rollback

Stage the candidate image in a separate project, using a current coordinated
checkpoint and unchanged lab-v1 schemas. The v1→v1.1 validation changes package
metadata while keeping business/storage code compatible. It is not a database
migration test. Unknown formats remain blocked. Before rollback, stop the new
project and take a NEW coordinated checkpoint containing its newest messages and
revocations; restore that current state into an isolated compatible older
package. Reusing the pre-upgrade snapshot would lose progress and is forbidden.
Incompatible future versions require a separately reviewed migration.

## 5. Status and Incident Handling

The local status CLI reports readiness separately from liveness/delivery and
uses fixed alerts for unavailable health, cloud disconnection, backlog,
quarantine, policy mismatch, impending credential expiry, byte/row capacity and
recorded quota/storage refusals. It suppresses tokens and payloads. Read current
live health when deciding whether data delivered; catalog history alone is not
current-channel proof. Record operator, UTC, package/image, alert codes, accepted/
ACK/committed/pending/quarantined counts and sanitized evidence references.

- Backlog/disconnection: check policy and credential validity, endpoint identity
  and cloud availability. Preserve event IDs. Never weaken TLS or clear queues.
- Expiry/mismatch: renew only a valid lease or issue authorized fresh leaves;
  confirm the new channel's ACK. Do not restore retired keys.
- Capacity/storage: stop source admission, preserve accepted data and inspect the
  fixed refusal reason. The unchanged source has no reading ACK or automatic
  replay. Socket send success is not acceptance; unknown in-flight losses stay
  unknown. Recovery needs an operator-reviewed source checkpoint.
- Unknown schema/integrity/receipt: isolate and retain state; block promotion.
  Do not edit DB versions or bypass guards. Record a bounded repair/review task.

## 6. Reproduce and Stop Experiments

scripts/phase_d/acceptance.py runs the actual100-sample/600-second checks in new
owned projects. --diagnostic is short and cannot satisfy those gates.
scripts/phase_d/endurance.py is a standalone 30-minute supervisor under the
explicit [human scope amendment](SCOPE_AMENDMENT.md). It uses
real time, five-second samples, lease renewal, rotation, Docker resource samples,
final reconciliation and a private cold checkpoint before owned cleanup. It is
not a recurring Codex task and does not publish code. A shorter diagnostic stays
explicitly non-accepting. See PAUSE_HANDOFF.md and RESUME_PROMPT.md for the stopped run and resume rules.
The human explicitly resumed D and changed its duration to1,800seconds. Renewal
remains every150seconds; both-role rotation is now every450seconds. Require at
least three real rotations. Earlier pause records and partial durations remain
historical; this experiment cannot establish24-hour operation.

To stop a supervisor, create its external runtime root's STOP file. Within one
sampling cycle it stops services, preserves a cold checkpoint where possible and
cleans only verified ownership-labelled resources. An interrupted/missing result
is not a pass. Keep Docker/host awake throughout the actual duration.
cleanup explicitly removes only this package's labelled containers/networks/
volumes; use it only after the needed cold checkpoint is verified. Private
artifact directories and cached images are retained for deliberate later cleanup.
