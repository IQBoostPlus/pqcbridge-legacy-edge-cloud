# Sprint 1 retrospective actions and follow-up

Status: preparatory record. No Sprint 1 retrospective meeting or student-team
outcome is recorded here. The actions below are proposed preventive work items;
they become agreed retrospective actions only after an actual team discussion.
The coordination task [SCRUM-13](https://tacczy.atlassian.net/browse/SCRUM-13) is To Do. Individual action
proposals below have local IDs and await team agreement before Jira entry.
The five-member roster is now available in [TEAM_REVIEW.md](TEAM_REVIEW.md).
Actual retrospective attendees, facilitator and action owners remain unconfirmed.
The user reports a group review was held without a saved original record; its
date, actual attendees, opinions and acceptance decision remain unconfirmed.
That review statement does not establish that a retrospective also occurred.
Current work responsibilities are recorded in TEAM_REVIEW.md. The team
confirms retrospective participation and action owners separately.
The later independent material review refreshed 11/11 model checks and sampled
screenshot-caption agreement. Its findings can inform the eventual
retrospective, but are not member observations or an agreed improvement action.

Scope: [SPRINT_GOAL.md](SPRINT_GOAL.md). Implementation stories:
[BACKLOG.md](BACKLOG.md). Process concerns:
[RISK_AND_DECISION_LOG.md](RISK_AND_DECISION_LOG.md).

## Proposed preventive actions

| Local ID | Trigger / proposed action | Completion evidence needed | State | Owner / Jira key | Follow-up |
| --- | --- | --- | --- | --- | --- |
| RA-S1-01 | Avoid inconsistent metrics: agree on coverage denominator, units and unknown behavior before building | D-03/D-04 and worked-result checks in VERIFICATION.md linked to S1-US-02 | Proposed; prototype rules and AI arithmetic checks recorded; team agreement pending | Unassigned / not created | Inspect actual discrepancies in Sprint 1 retrospective; carry any agreed action to Sprint 2 |
| RA-S1-02 | Avoid process evidence gaps: update stories and logs with actual findings at each build batch | Build and artifact-preparation entries in LLM_EVALUATION.md; [story mapping](BACKLOG.md) is in place, with ongoing updates to be agreed | Proposed; per-batch records maintained and initial Jira mapping confirmed; team adoption pending | Unassigned / not created | Inspect one completed story at the retrospective; check follow-through during Sprint 2 planning |
| RA-S1-03 | Avoid a last-minute unusable demo: run a small integrated browser walkthrough before adding optional scope | Working parent-observed walkthrough and screenshots in VERIFICATION.md | Proposed; implemented dashboard and AI walkthrough evidence available; team review pending | Unassigned / not created | Discuss the observed integration friction; follow agreed improvement in Sprint 2 |
| RA-S1-04 | Avoid confusing stakeholders: have students walk through all three roles and record misunderstandings | Named participants, task/scenario, observed misunderstanding, resulting change; label role-play as simulated | Proposed; participation pending | Unassigned / not created | Review actual feedback at the retrospective; verify any carried fix in Sprint 2 |

These proposals are not evidence that the team experienced a problem or learned
a lesson. Team members may accept, revise or reject them with recorded reasons.

## Actual retrospective record to complete at the meeting

### AI build observation for later discussion

During the first build batch, the integrating AI needed an explicit data contract
before independent model and UI subagents could implement safely. It selected
and recorded the denominator, demo clock, freshness, status precedence and
invalid-snapshot policy in decisions D-03/D-04/D-07. This is an AI workflow
observation, not a student account of teamwork or a retrospective finding.

RA-S1-01 now has a recorded prototype rule and parent-checked arithmetic as
partial evidence; team agreement remains pending. RA-S1-02 has actual delegated
per-batch log maintenance and AI output evaluation recorded. RA-S1-03 has a
parent-observed working browser walkthrough; full mobile visual validation is
still open after a screenshot-capture failure. Actual student participation for
RA-S1-04 remains pending. A proposed discussion question is
whether the contract reduced integration mismatches, supported by the actual
test-expectation correction and [verification record](VERIFICATION.md). No retrospective action is marked
accepted or completed by these AI notes.

### Meeting record

| Field | State |
| --- | --- |
| Meeting date, participants and facilitator | Pending actual meeting |
| Sprint goal outcome and evidence examined | Pending actual meeting and increment |
| What helped, supported by concrete examples | Pending participant observations |
| What impeded work, supported by concrete examples | Pending participant observations |
| Differences in stakeholder interpretations or team communication | Pending participant observations |
| Agreed actions, priority and expected improvement | Pending team decision |
| Assigned owner, target date and actual Jira key for each action | Pending team assignment and Jira transfer |
| Sprint 2 follow-up date, evidence and outcome | Pending next sprint |

At the retrospective, append actual findings and link the relevant risk,
decision or story. For each agreed action record owner, due date, Jira key,
completion criterion and next-sprint review. Preserve rejected proposals and
their rationale rather than relabelling them as completed work. During Sprint 2,
record whether each action happened and whether the intended improvement was
observed, with evidence or an explicit explanation for carrying it forward.

### Verified AI build observations for the eventual retrospective

The parent reported 11/11 passing model checks and observed the working default
fixture, three roles, filters and data-error/reset behavior. The initial model
checks required correcting a mistaken search expectation; record this as a
lesson candidate about independent expected results, not a product failure or
a student learning claim. A stale one-PQC scenario retained 100% coverage while
showing UNKNOWN overall, illustrating why progress and evidence quality need
separate explanations. No real retrospective meeting is implied by this note.

Potential follow-up for actual team discussion: ask students to interpret that
stale scenario and capture their own misunderstandings. Team members decide
whether to adopt this action, assign an owner and create the real Jira issue.
