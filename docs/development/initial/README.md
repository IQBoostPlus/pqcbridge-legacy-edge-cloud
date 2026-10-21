# Initial Development Records: P01–P08

These records describe the initial simulation baseline, security design, corrective implementation, and verification sequence. They are historical evidence, not a description of every capability or limitation of the current engineering path.

## Record Index

| Phase | Record | Purpose |
| --- | --- | --- |
| P01 | [Baseline design and requirements](P01-Baseline-Design.md) | Initial architecture, requirements, deliverables, and reported baseline evidence |
| P02 | [Baseline technical review](P02-Baseline-Technical-Review.md) | Findings F-01–F-15, demonstrations, and test gaps |
| P03 | [Security evaluation and design decisions](P03-Security-Evaluation-and-Design-Decisions.md) | Proposed decisions, alternatives, priorities, and verification design |
| P04 | [Security implementation and verification](P04-Security-Implementation-and-Verification.md) | Selected fixes, fail-first tests, integration checks, and limitations |
| P05 | [Independent security verification](P05-Independent-Security-Verification.md) | Re-testing, NEW-1 discovery, and observed limitations |
| P06 | [Nonce validation and security verification](P06-Nonce-Validation-and-Security-Verification.md) | Targeted NEW-1 fix and regression verification |
| P07 | [Evaluation and evidence consolidation](P07-Evaluation-and-Evidence-Consolidation.md) | Consolidated finding status, evidence, and remaining risks |
| P08 | [Adversarial testing and remediation](P08-Adversarial-Testing-and-Remediation.md) | BF findings, compound effects, scoped remediation, and residual risk |

Each phase has a `Pxx-REQUIREMENTS.md` companion containing its historical technical specification. The [coverage ledger](REQUIREMENTS_COVERAGE.md) records which original numbered sections were retained and which role/response scaffolding was omitted. Requirements express intended work; the phase report establishes what was observed or implemented.

## Editorial and Provenance Notes

On 2026-10-18, the initial reports were organized as engineering development records. The original baseline, reports, and proposed decisions involved AI assistance. This reorganization does not recast that work as independently human-authored or treat pending human review as completed. Automated independent testing is distinct from external human security approval.

The technical bodies of P02–P08 retain their findings, test outcomes, code examples, decision states, and limitations. Headings and navigation were updated. Historical observations about the README, course deliverables, absent Docker, or the repository's earlier state describe their original phase. They are not claims about the repository today.

The P01 record was reconstructed from its specification and P02's baseline context. No new runtime tests or attack reproductions were performed for this editorial update. Historical test counts remain attached to their original phases.

Original task specifications were removed from the active tree after migrating their technical content. Their complete original wording and the earlier reports remain recoverable in Git history before the documentation reorganization. Original section numbers are preserved in the requirements companions so references such as “P04 section 11” remain interpretable. Legacy source comments and verbatim evidence blocks may retain historical path names; use the phase number and this index to resolve them. Runtime source and evidence files were not rewritten merely to change those comments.

AI-use or authorship disclosures required by a particular competition, license, or institution must reflect actual contributions. The README's product presentation does not replace those obligations.

## Continuing the Development Record

Use the [development record guide](../README.md) and [template](../RECORD_TEMPLATE.md) for future milestones. Keep the same evidence-first style: scope, concrete findings, decisions, implementation, verification, and remaining risk. Record results only after observation and preserve failed experiments when they explain a change.

Current engineering evidence is maintained separately in [Phase A](../../phase-a/STATUS.md),
[Phase B](../../phase-b/STATUS.md), [Phase C](../../phase-c/COMPLETION.md) and
[Phase D](../../phase-d/COMPLETION.md). Their acceptance is limited to the owned
Docker/simulated-device lab, with D sustained acceptance covering 30 minutes.
See the [project report](../../PROJECT_REPORT.md) for consolidated results and
the [real-device plan](../../REAL_DEVICE_PLAN.md) for future physical/Web/AI work.
No physical-device or production acceptance is established by these records.
