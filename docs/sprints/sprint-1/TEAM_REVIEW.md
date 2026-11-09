# Sprint 1 team register and review record

## Confirmed membership

The user supplied the following five members in the project chat. Names are
recorded exactly as supplied; roster membership does not establish attendance,
individual contributions or acceptance of the increment.

| Member | Membership source | Current Sprint 1 responsibility |
| --- | --- | --- |
| Changzhengyuan Chu | User-provided roster | Jira, project documentation and submission coordination |
| Valerii Lebedev | User-provided roster | Video recording |
| Jinghao Lei | User-provided roster | Interface, role views and accessibility |
| Cheng Peng | User-provided roster | Testing, security concept checks and verification records |
| Zhizhou Zhao | User-provided roster | Sprint report and PowerPoint slides |

The user supplied this allocation for current work. Member acknowledgement,
historical contributions and formal Jira assignees are tracked separately.
The teacher retains the Product Owner role. The separate Scrum Master proposal
remains subject to team confirmation: Changzhengyuan Chu for Sprint 1,
Valerii Lebedev for Sprint 2 and Jinghao Lei for Sprint 3.

## Product vision and stakeholder review basis

Provide a repeatable synthetic-data dashboard that lets security, migration and
executive stakeholders understand the same PQC transition through information
suited to their decisions, with visible uncertainty and business consequences.

| Persona | Decision supported | Conflict to discuss |
| --- | --- | --- |
| Sarah, security officer | Investigate non-PQC exposure and suspected downgrade using context and confidentiality assumptions | Wants fallback removed quickly; cannot treat a migration percentage as proof of safety |
| Michael, migration manager | Prioritize remaining segments, blockers and legacy replacement exceptions | Needs monitoring continuity while replacements are unavailable; exceptions retain residual exposure |
| Emma, CIO | Understand status, three main risks and business actions | Must balance continuity, budget and delivery commitments; a simple color must retain its explanation |

The prototype separates progress, uncertainty and investigation needs. It
provides decision support rather than automatically resolving this conflict by
blocking devices. Approved exceptions in a synthetic scenario do not eliminate
the corresponding exposure. Team and teacher/PO review of these choices is pending.

## Evidence-based technical review

The user confirmed that a group review took place and that its original record
was not saved. The actual date, attendees, member comments, decisions and
acceptance conditions have not been supplied. This record reconstructs the
evidence and prepares discussion points for confirmation; it does not reconstruct
unknown historical statements as facts. A separate independent AI technical and
material review was conducted for the group.

| Story | Evidence available for discussion | Current assessment |
| --- | --- | --- |
| S1-US-01 | Fixed JSON fixture, schema validator, invalid-input/reset browser evidence | Implemented; AI verification recorded; student acceptance pending |
| S1-US-02 | 8 = 5 PQC + 2 fallback + 1 unknown; 5/8 = 62.5%; empty/unknown/stale examples | Calculations and limitations recorded; student interpretation pending |
| S1-US-03 | Filter results: fallback 2, unknown 1, PQC 5; mixed device/cloud path and row context | Browser evidence recorded; student walkthrough pending |
| S1-US-04 | Sarah, Michael and Emma panels; common data; business impacts and next actions | Three views implemented; actual user usefulness review pending |
| S1-US-05 | Formula, 24-hour freshness, historical/current clocks, qualified status and HNDL explanations | Rules documented and AI-checked; team/PO approval pending |

Source evidence: [verification](VERIFICATION.md), [backlog](BACKLOG.md),
[risk/decision log](RISK_AND_DECISION_LOG.md), [LLM evaluation](LLM_EVALUATION.md)
and the local six-image gallery (`submission/Sprint1_Dashboard_Images.md`).

Independent review result: 11/11 model tests passed on this review turn; the
reviewer independently confirmed fixture counts and all six image references,
and visually checked the executive and fallback screenshots against captions.
No actionable implementation/material defect was identified within the approved
synthetic-data scope. The conclusion is readiness for factual student review,
not teacher/PO approval or a completed Moodle submission.
Historical browser results remain historical evidence; this document does not
claim a new live browser walkthrough or a human usability test.

## Student walkthrough: expected results prepared

These questions and expected answers are prepared for the group. The response
column records the actual missing evidence rather than invented member feedback.

| Review question | Expected explanation from the prototype | Actual student response / decision |
| --- | --- | --- |
| Why is coverage 62.5%? | Five PQC segments out of eight total; the unknown segment remains in the denominator | Not yet supplied |
| Is every fallback a downgrade attack? | No. SEG-001 is an expected synthetic legacy exception; SEG-007 has an explicitly unconfirmed investigation scenario | Not yet supplied |
| Is Pump station A protected end to end? | Its gateway-to-cloud segment reports PQC, but its device-to-gateway segment remains classical | Not yet supplied |
| Can 100% coverage coexist with UNKNOWN overall status? | Yes. Stale observations can report past migration without supporting a current all-clear | Not yet supplied |
| What should the executive decide next? | Investigate the suspected downgrade, resolve missing evidence and prioritize exceptions/replacements with business continuity in mind | Not yet supplied |

## Discussion points and modification requests for member confirmation

The following are prepared discussion candidates, not quotations or confirmed
opinions from the earlier meeting. Confirm, revise or reject each item before
attributing it to a member or reporting it as a group decision.

| Assigned follow-up lead | Discussion candidate | Proposed modification / completion criterion |
| --- | --- | --- |
| Changzhengyuan Chu | Process evidence needs to be traceable to Jira | Use the ten mapped issues to track current progress and confirm estimates, assignees and actual dates with the team |
| Valerii Lebedev | The video needs a focused demonstration of the accepted scope | Record the dashboard walkthrough using the final slides and check the five-minute limit |
| Jinghao Lei | Reported 100% migration can still be misunderstood when evidence is stale | Run a student role walkthrough and complete mobile/keyboard checks; consider moving overall evidence quality nearer the overview only if the walkthrough supports that change |
| Cheng Peng | AI-authored tests and screenshots need student evaluation | Reproduce critical arithmetic, fallback classification and invalid-input recovery checks; record expected/observed results and any actual defects |
| Zhizhou Zhao | The report and slides should tell the same evidence-based Sprint story | Review the report against the Sprint evidence and prepare the slides used in the video |

No code change is justified solely by these candidates. Prioritize actual defects
and PO feedback; confirm scope before adding usability changes.

## Working agreement proposal and Scrum roles

The following is a proposal to confirm, not a record of practices already
followed by the five students:

- Use Jira as the course backlog/progress record; keep repository evidence
  linked to real issue keys after transfer.
- Choose one team communication channel and record actual planning, review and
  retrospective dates/participants. Platform and meeting arrangements are open.
- Use the Sprint goal and explicit acceptance criteria for scope decisions.
  Record alternatives and rationale in the decision log.
- Resolve disagreements by checking evidence and stakeholder consequences;
  the Scrum Master facilitates, and the teacher/PO resolves scope priorities.
- Confirm the prospective Scrum Master allocation and rotation above. Record
  the actual facilitator of the earlier review separately if different.
- Review generated content personally; distinguish AI checks from student and
  teacher acceptance. Give each agreed action an actual owner and target date.

Teacher/PO: the course teacher, as specified by the course materials.
The current work allocation and proposed Scrum Master rotation are recorded above. Acknowledgement, historical
contribution evidence, communication channel and team agreement await confirmation.

## Follow-up actions prepared for confirmation

| Action | Priority / completion criterion | Owner and target |
| --- | --- | --- |
| Confirm roles, contributions and working agreement | Before submission: confirm prospective roles and record historical contributions and communication choices | Changzhengyuan Chu; before Sprint 1 submission |
| Confirm Jira planning fields | The mapping and statuses are recorded in [BACKLOG.md](BACKLOG.md); confirm team estimates, priorities, assignees and actual Sprint dates in [SCRUM-10](https://tacczy.atlassian.net/browse/SCRUM-10) | Changzhengyuan Chu coordinates; before Sprint 1 submission |
| Recover review evidence and evaluate generated work | Record actual participants, feedback, acceptance conditions and student evaluation | Changzhengyuan Chu coordinates; Cheng Peng records validation; before final report |
| Hold retrospective and agree improvements | Record actual observations and agreed actions; follow them in Sprint 2 | Proposed Scrum Master facilitates in Sprint 1; confirm the Sprint 2 follow-up owner with the team |
| Review reporting rules with PO | Obtain feedback on denominator, clock and status precedence | Cheng Peng prepares verification evidence for the next PO discussion; confirm the meeting owner with the team |
| Check remaining mobile/accessibility concerns | Record actual results and prioritize material usability defects | Jinghao Lei with Cheng Peng; review before submission and carry unresolved items into Sprint 2 |
| Finish Moodle artifacts | In [SCRUM-14](https://tacczy.atlassian.net/browse/SCRUM-14), verify the report PDF, combined dashboard-image PDF, video of at most five minutes and PDF of the slides used | Changzhengyuan Chu coordinates; Zhizhou Zhao prepares the report and slides; Valerii Lebedev records the video; all five check content by the course deadline |

## Human review and acceptance record

The user confirmed the Jira setup separately from the earlier group review.
[SCRUM-13](https://tacczy.atlassian.net/browse/SCRUM-13) is To Do and tracks review findings and retrospective
actions as distinct outcomes. The board's In Review story status reflects
pending acceptance.

| Field | Current evidence |
| --- | --- |
| Review occurrence | Held, according to the user's confirmation; original minutes were not saved |
| Review date and location/channel | Not retained / not yet supplied |
| Actual attendees and facilitator | Not yet supplied; the roster above is not an attendance list |
| Individual feedback and evaluation of generated output | Not yet supplied |
| Team acceptance decision and conditions | Not yet supplied |
| Teacher/PO feedback and decision | Not yet supplied |
| Accepted actions, owners and deadlines | Not yet supplied |

The group can recover the missing evidence through a short factual meeting
summary or confirmation of remembered points. Preserve the technical findings above and append actual decisions;
only then update acceptance claims in the report and backlog.
