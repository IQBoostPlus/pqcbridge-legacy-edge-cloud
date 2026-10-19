# Phase C execution specification

Started2026-10-17; paused2026-10-18, explicitly resumed and completed2026-10-19.
Accepted for owned Docker/simulation after matching-source lifecycle verification,
independent reviews and final reconciliation. STATUS/COMPLETION/REVIEW and
FINAL_AUDIT supersede the historical pause handoff and interrupted run.
Baseline B a6a083acac5afc06b81e82d4568e775069883ac1; integration branch
codex/phase-c-management. Preserve original user edits, V1/config/state and B
delivery semantics. Snapshot: tmp/phase-c-start-d0b52ec232dd473f91304fe3eaab229a.
Scope remains owned local Docker/synthetic identities. No management web platform.

## Selected management boundary

A local operator CLI owns a separate bounded durable catalog/audit database and
atomically exports a read-only trusted manifest. The controller/issuer is trusted
local administration, not an unauthenticated network service. The service has no
issuer private key and no per-message controller call. Credential references and
public certificate metadata are stored in the catalog, never source keys, health
tokens or private-key bytes. Credentials remain outside checkout and role mounts
stay separate. Local host compromise is outside this lab protection boundary.

The fixed policy profiles are hybrid-standard-v1 (5s operation cap) and
hybrid-conservative-v1 (3s cap). Both require TLS1.3, mTLS, X25519MLKEM768 and no
0-RTT. No classical downgrade or arbitrary algorithm menu. Changes target a
gateway channel group. Cloud authorization refresh is per gateway, preserving
unmodified groups. Identity/incarnation/message namespace and pending bytes do
not change during policy or certificate rotation.

## Shared manifest contract (schema_version 1)

Top-level fields: schema_version, sequence (strictly increasing publication),
issued_at/expires_at (UTC; <=300s lease), cloud_credential (fingerprint),
credentials (fingerprint -> descriptor), targets (gateway_id -> target).
Descriptor fields: role (gateway/cloud), subject_id, cert_file, key_file,
not_before, not_after, revoked (boolean). References are absolute container paths;
certificate lifetime <=24h. Fingerprints are verified leaf DER SHA256 lowerhex.
Target fields: enabled, version (positiveint), profile, active_credential,
accepted_credentials (fingerprint -> absolute overlap deadline or null for active),
devices (device_id -> source incarnation UUID). A disabled asset is not authorized.
At most3 gateways,3 devices/gateway,12 credential descriptors,100 policy versions,
1000 audit operations; catalog budget32MiB, no automatic deletion. Overlap <=60s.
Retired/expired/revoked credentials are never restored by profile rollback.
Catalog export <=65535bytes. Operator records are nonempty bounded identifiers.

ManagementStore public interface is specified for exclusive workers below:
enroll_gateway, enroll_device, set_enabled, register_credential, revoke_credential,
create_version, begin_apply, observe, rollback, status, manifest, export, audit,
close. A version selects a known profile and active gateway credential plus a
bounded accepted-certificate overlap. Rollback restores a prior safe profile via
a new publication sequence, retaining current valid nonrevoked credentials.
Pending/Applying/Effective/Failed/Rolled back/Unknown are distinct statuses.
Effective requires fresh real authenticated channel plus post-apply matching
business ACK; stale observation becomes Unknown. CLI operator observations are
privileged audit claims; runtime acceptance must obtain actual protected health
evidence, not manufacture test records as proof of live effectiveness.
Disconnected runtime objects also report Unknown. Successful catalog observations
must carry runtime management_state=Effective and management_applied_at, proving
the ACK is at or after the current channel's bind time as well as after the
operator apply boundary. Missing or prior-channel proof is refused atomically.

## Service integration

Opt-in managed bootstrap reuses B Service and storage via ManagedConfiguration.
Base B config supplies private source keys, token, endpoints, budgets and state.
Its additional management object names an absolute manifest_file. ManagedConfiguration
implements B value/tls/limits/token/state_dir/remaining/valid contract and adds
channel_token(peer_fingerprint), channel_current(peer_fingerprint, token),
management_status(), source_allowed(device_id, spec), operation_timeout(peer_fingerprint=None).
The timeout API is a method; public configuration validation needs no fake TLS
initialization, while managed bootstrap/context still enforce the actual TLS gate.
Cloud token changes only for affected peer authorization/profile or own TLS leaf;
gateway token changes on its target/version/own credential or accepted cloud leaf.
Runtime binds tokens after TLS, rechecks within idle1s and whole-frame<=5s, and
rebuilds cloud TLS context for new handshakes when managed. Revoked/disabled peers
lose active and new access; authorized source may still buffer within B quota
when cloud policy is expired. Device disabling closes its source channel.
Persist highest manifest sequence/revocation tombstones in the role state directory
to refuse old control snapshots after restart. No source/dedup-state reset.

## Acceptance and workflow

Continue the approved public CLI/process, socket/TLS, protected HTTP and durable
public storage API boundaries; no private SQL acceptance or fake ACK evidence.
Use red-green verticals and exclusive module ownership, root integration, then
independent Standards/Spec reviews. Catalog/issuer tests do not establish service
acceptance. Actual Docker must exercise a live policy migration, failed migration
and safe rollback, bounded credential overlap/retirement, failed rotation recovery,
emergency revocation including active disconnection, disabled assets, unknown/
weakened profiles, stale evidence and controller-offline lease/certificate expiry.
Use two gateway groups to verify a failed canary does not disturb the other group.
Shortened expiry fixtures measure the same enforcement path; report duration.
No claim of online OCSP/CRL or instantaneous offline revocation: last accepted
lease bounds offline authorization to5min (plus measured bounded scheduling).
Full regression, source/evidence reconciliation and owned cleanup precede C
acceptance and authorized major-phase publication. D remains future.
