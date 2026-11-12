# Sprint 2 goal and delivery record

## Goal and authority

Make the synthetic dashboard's indicators traceable and independently
checkable, then evaluate whether security, migration and executive users can
interpret the same evidence and choose a justified next action.

Planning baseline: **12 November 2026**. The user instructed that indicator
credibility must come first, followed by a user-understanding experiment and
Sprint 2 records following the Sprint 1 structure. This establishes the local
planning priority. The user subsequently confirmed that this priority was a
group discussion decision. The original meeting date and minutes were not supplied.
Teacher/Product Owner acceptance, estimates, Sprint dates and Jira transfer
are not yet recorded.

Current delivery state: **indicator evidence features implemented; 17 model
tests, production build, 11 scenario comparisons and scoped desktop/mobile
browser checks passed; human comprehension study and team/PO acceptance
pending**. The [group discussion record](TEAM_REVIEW.md) separates the user's
instruction, technical findings and actual group feedback. No attendance or
participant answers are inferred from the Sprint 1 roster.

## Committed planning scope and proposed increment

The records below implement the requested planning work. Product stories are a
proposed Sprint commitment until team/PO planning. The user subsequently
authorized development against this goal. Sprint 2 adds traceability and export
features; existing Sprint 1 calculations remain baseline behavior.

| Order / story | Increment | Observable acceptance |
| --- | --- | --- |
| 1 / S2-US-01 | Explicit indicator contract | Review formula, numerator, denominator, segment unit, source, observation/snapshot/reporting clocks, 24-hour boundary, classification assumptions and status precedence. Every displayed conclusion can be traced to input records and a rule; unknowns remain in scope. |
| 2 / S2-US-02 | Independent evidence for indicator credibility | Retain inputs, independently stated expectations and actual results for default, filtered, empty, unknown, stale, future, mixed-path, expected/suspected fallback and invalid data. Review both arithmetic and interpretation. Human approval of rules remains separate. |
| 3 / S2-US-03 | Three-role comprehension experiment | After the metric evidence gate, run the protocol in USER_UNDERSTANDING_EXPERIMENT.md with consenting actual participants. Preserve first answers, evidence locations, errors and decisions; distinguish AI rehearsal from human results. |
| 4 / S2-US-04 | Feedback-driven usability corrections | Prioritize observed misunderstandings or reproducible defects, document a before/after example and recheck affected scenarios. If no change is justified, record that decision with actual evidence. |
| 5 / S2-US-05 | Follow-through on process improvements | Discuss Sprint 1 proposed retrospective actions, record accepted/rejected decisions and assign real owners/dates. Review resulting evidence in Sprint 2. |

The [backlog](BACKLOG.md) contains acceptance criteria and dependencies. Priorities
are explicit: complete the metric evidence gate before interpreting comprehension
results or committing interface changes.

## Indicator contract and acceptance gate

- Coverage = PQC segments / all in-scope segments, including unknowns, multiplied
  by 100; display rounds to one decimal. Empty coverage is unavailable.
- Coverage describes reported connection segments. A migrated gateway-to-cloud
  link does not establish migration of the device's complete path.
- Freshness is per observation against the selected reporting clock. Exactly
  24 hours is current; older observations are stale. Historical mode uses
  snapshot time; current-time mode re-evaluates the same observations.
- Overall precedence is suspected downgrade -> investigate; otherwise
  empty/unknown/stale/future evidence -> insufficient evidence; otherwise
  expected fallback -> migration remaining; otherwise qualified reported migration.
  Red may coexist with missing/stale evidence; all relevant reasons must remain
  available for interpretation.
- Filtering changes inventory rows, not the global coverage denominator.
- Fallback classification and confidentiality lifetimes come from synthetic
  inputs. Suspected downgrade is not a confirmed attack; HNDL exposure is an
  assumption-based explanation; migration is not a security guarantee.
- Invalid data must remain distinguishable from a valid empty snapshot.

Gate: independent expected/observed comparisons pass, discrepancies are resolved
or explicitly block acceptance, rule/source references are checked, and the team
reviews the metric contract. This batch supplies technical evidence; it does not
complete the human review gate.

## Implementation boundaries

Continue using the independently runnable synthetic Vue dashboard. This batch
implements indicator traceability, evidence export and source-supported
interpretation improvements, with a participant kit for the human experiment.
Real-time backend ingestion, authentication, databases, automatic blocking,
protocol redesign and new risk-scoring formulas are not selected for this plan.
The PQC communication prototype remains a separate demonstration.

## Build sequence and evidence

1. Agree the indicator contract and record outstanding questions.
2. Reproduce baseline tests and the independent scenario rehearsal; review any
   differences between source behavior and stakeholder interpretation.
3. Confirm participants and run the human protocol without giving answer keys
   before first responses. Record actual group discussion results afterward.
4. Select and implement only evidence-supported corrections; review generated
   output and verify calculations plus affected browser workflows.
5. Hold the review and retrospective, evaluate carried actions, update Jira and
   record team/PO acceptance separately from technical checks.

Definition of Done: accepted story criteria are demonstrated, significant AI
outputs are reviewed, metric and affected browser checks are recorded, human
study evidence supports comprehension claims, documentation matches behavior,
and residual risks plus team/PO acceptance are explicit. Technical implementation
and verification are complete within the recorded scope; human evaluation and
acceptance remain open in the increment's Definition of Done.

## Supporting records and delegation

| Artifact | Purpose |
| --- | --- |
| [Backlog](BACKLOG.md) | Ordered stories, acceptance criteria and future Jira mapping |
| [Risk and decision log](RISK_AND_DECISION_LOG.md) | Metric, interpretation, scope and evidence risks |
| [Experiment](USER_UNDERSTANDING_EXPERIMENT.md) | Executed AI rehearsal and pending human study protocol |
| [Verification](VERIFICATION.md) | Commands, observed results and verification boundaries |
| [Team review](TEAM_REVIEW.md) | Group discussion results, authority and pending feedback |
| [LLM evaluation](LLM_EVALUATION.md) | Prompt/output provenance and evaluation |
| [Retrospective actions](RETROSPECTIVE_ACTIONS.md) | Proposed carry-over and actual follow-up |

As in Sprint 1, each construction batch uses bounded delegated record work with
exclusive ownership. The integrating agent reconciles claims, verifies the
assembled increment and updates README/project instructions. Repository records
are English. Real Jira actions, meetings and PO decisions require their own
evidence; local story IDs are not Jira issue keys.

## Sprint submission checklist

- [x] Record the user-directed priority and ordered Sprint 2 proposal.
- [x] Prepare indicator contract, independent scenarios and AI role rehearsal.
- [x] Establish backlog, risks, AI evaluation and retrospective records.
- [x] Record the user-confirmed group decision: indicator credibility first.
- [ ] Review discussion points and approve the indicator contract with the team.
- [ ] Confirm Sprint dates, estimates, owners, Scrum roles and Jira mapping.
- [ ] Run and record actual human comprehension sessions and group discussion.
- [x] Implement and technically verify source-supported indicator corrections;
      additional corrections depend on actual participant findings.
- [ ] Complete team/PO review and retrospective with actual decisions.
- [ ] Confirm Sprint 2 course submission requirements before preparing artifacts;
      Sprint 1 dates and submission limits do not establish Sprint 2 requirements.

## Change record

| Date / event | Authority or evidence | Result |
| --- | --- | --- |
| 2026-11-12 / planning priority | User instruction in project chat | Indicator credibility first, then comprehension evaluation; records created following Sprint 1 |
| 2026-11-12 / baseline and AI rehearsal | VERIFICATION.md and experiment evidence | Technical baseline checked; no human comprehension or group acceptance inferred |
| 2026-11-12 / clarification | User confirmed group priority | Indicator credibility first recorded as a group decision; discussion draft prepared |
| 2026-11-12 / development authorized | User instructed Sprint 2 development against this goal | Indicator audit, shared traceable evidence, export, global denominator and path context implemented; participant kit prepared |
| 2026-11-12 / integrated verification | VERIFICATION.md | 17 tests, build, 11 comparisons, desktop/mobile browser workflows and downloaded JSON checks passed; human/PO acceptance pending |
