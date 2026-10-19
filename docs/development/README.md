# Development Documentation Guide

Write all project documentation in English. Use Chinese when communicating with the user.

## Organization

- [Initial Development Records](initial/README.md) retain P01–P08 history and its technical requirements.
- [Phase A](../phase-a/STATUS.md), [Phase B](../phase-b/STATUS.md) and [Phase C](../phase-c/STATUS.md) retain engineering execution reports and evidence. Preserve historical status and raw results.
- Current C records: [migration milestone](../phase-c/COMPLETION.md), [management operations](../phase-c/OPERATIONS.md) and [Linux CI follow-up](../phase-c/CI_FIX.md). D has not started.
- Subsequent milestones use the [record template](RECORD_TEMPLATE.md), adapted to the actual work. Keep related evidence and runbooks with the relevant phase.
- The [engineering roadmap](../ENGINEERING_ROADMAP.md) defines direction; execution records establish implementation and acceptance. Update current navigation without rewriting historical outcomes.

## Writing Style

Use the revised P01–P08 records as the reference: direct technical prose, numbered sections, explicit scope, stable finding identifiers, concise comparison tables, and concrete evidence. A record should explain the problem and outcome before implementation detail. Prefer one record per meaningful milestone rather than one per chat or small edit.

For a finding, state its ID, affected component, preconditions, observed behavior, consequence, evidence, decision, and remaining risk. Preserve the distinction between a proposed decision, an implemented change, and an accepted result. Include unexpected failures and test-harness defects when they affect confidence in a result.

## Evidence and Acceptance

Identify the source revision, relevant local changes, environment, exact workload, dependency versions, and evidence paths. Separate static inspection, automated tests, live application tests, and environment-limited checks. Historical numbers must be labeled historical; proposed thresholds must not be presented as measurements. Do not add overlapping test counts into a stronger assurance claim.

Retain raw result files and existing evidence hashes. When documents move, update navigation or provide a historical reference map; do not alter source or evidence bytes merely to make archived comments look current.

Document AI assistance and reviewer identity when material to provenance or required by the target event. Do not invent human review or independent authorship. A passing automated review is not production security certification.

## Publication

When the user authorizes GitHub publication, create a scoped English commit and push directly to the intended branch. Do not create a pull request unless the user explicitly changes this preference. Preserve unrelated work, exclude credentials and runtime state, use ordinary non-forced pushes, and verify the remote commit SHA.

The direct-push preference describes the publication method; it is not permission to publish incomplete phases or unrelated work automatically.

## Closing Documentation Check

Before declaring a task, phase, scheduled run or publication complete, compare README.md, PROJECT_STATE.md, the short-term plan, current phase status, operations/recovery instructions and navigation with verified implementation, runtime evidence, CI and remote publication. Update stale current statements and broken links; distinguish implementation, local validation, accepted scope and actual publication. Preserve V1 content, archived findings and raw evidence bytes. Include necessary documentation changes with the corresponding scoped commit where possible. For an already published result, a separate factual documentation correction is allowed; avoid timestamp-only commits and recursive updates of a document to its own commit SHA. Preserve unrelated user edits and use explicit reviewed paths/hunks. With no factual drift, make no changes or repeated status notifications.
