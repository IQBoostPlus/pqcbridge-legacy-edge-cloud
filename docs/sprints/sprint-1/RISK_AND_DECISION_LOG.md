# Sprint 1 risk and decision log

Status: AI-assisted build record; group review reported held by the user,
with retained minutes and confirmed findings unavailable.
The [Sprint goal](SPRINT_GOAL.md) is the scope authority; [BACKLOG.md](BACKLOG.md)
contains the verified local-to-Jira mapping. Current work responsibilities
are recorded separately from Jira assignees in TEAM_REVIEW.md.
The user-supplied roster is recorded in [TEAM_REVIEW.md](TEAM_REVIEW.md);
membership does not establish past participation or acceptance.
The course deadline recorded earlier in the project chat is 11 November 2026,
23:59 Finnish time; subsequent course changes require PO confirmation.

## Initial risks

Likelihood and impact are provisional qualitative planning judgments. Suggested
owner roles below are assignment proposals, not claims that people accepted work.
All risks remain open with AI mitigation checks recorded below. The first
dashboard increment is implemented and AI-verified within the synthetic-data
boundary; prospective owner acknowledgement and student/PO acceptance remain pending.

| ID | Risk and effect | Likelihood / impact | Mitigation and verification needed | Suggested owner role | Related story |
| --- | --- | --- | --- | --- | --- |
| R-01 | HNDL exposure is presented as a detected attack, or every fallback is labelled malicious, misleading Sarah | Medium / High | Describe exposure assumptions; distinguish expected fallback from suspected downgrade; review labels against worked scenarios | Domain reviewer, unassigned | S1-US-04, S1-US-05 |
| R-02 | Unknown connections disappear from the denominator or zero records display 100% coverage | Medium / High | Keep unknown segments in total; show numerator/denominator; verify hand-calculated, empty and unknown-only datasets | Implementation reviewer, unassigned | S1-US-01, S1-US-02 |
| R-03 | ML-KEM on gateway-to-cloud is treated as PQC protection of the entire device path | Medium / High | Identify segments explicitly in rows and summaries; demonstrate a mixed-protection path | Domain reviewer, unassigned | S1-US-01, S1-US-03 |
| R-04 | Existing symmetric preconfigured-key device traffic is assumed to be the course's classical-key-exchange scenario | Medium / High | Maintain an independent synthetic model; identify key-establishment assumptions and confidentiality lifetime; review interpretation before reuse | Domain reviewer, unassigned | S1-US-01, S1-US-05 |
| R-05 | Scope growth or backend dependencies prevent a runnable increment by the deadline | Medium / High | Build fixed-data dashboard first; track optional work separately; demonstrate a small working version before adding scope | Sprint facilitator, unassigned | S1-US-01 through S1-US-05 |
| R-06 | LLM output invents facts, computes metrics incorrectly or claims unperformed validation | Medium / High | Retain prompt/output references; review code and wording; record independent arithmetic and browser checks in the LLM evaluation | Integrating reviewer, unassigned | All stories |
| R-07 | Local documents are mistaken for Jira history or actual Scrum participation | Medium / High | Mark local IDs and transfer state; add real Jira keys only after transfer; record meetings, PO feedback and assignments when they occur | Backlog coordinator, unassigned | All stories |
| R-08 | Overall status hides stale/unknown data or combines progress and security into an unexplained green score | Medium / High | Agree on freshness and status rules; show rationale and remaining exposure; exercise stale/invalid datasets | Domain and UI reviewers, unassigned | S1-US-02, S1-US-04, S1-US-05 |
| R-09 | A supplied team roster is mistaken for agreed roles, completed work or human review, creating inaccurate course-process evidence | Medium / High | Record the roster source separately from assignments; obtain actual role/contribution confirmation and review opinions/sign-off; keep AI material review labelled | Team process coordinator, unassigned | All stories and process tasks |

At each build batch or PO change, update likelihood/impact, mitigation evidence,
owner and residual risk. Close a risk only with an evidence reference and reviewer;
planned mitigations do not establish closure. Append significant changes below.

## Decisions and proposals

User scope approval is distinct from teacher/PO approval. No teacher decision is
recorded by this initial draft.

| ID | Topic and alternatives | State and authority | Rationale / consequences | Evidence or next review |
| --- | --- | --- | --- | --- |
| D-01 | Fixed synthetic-data dashboard with overview, connection filter, three role views and indicator explanations | Confirmed scope: user accepted the five-feature proposal and instructed construction in chat | First implementation batch implemented; AI checks passed | SPRINT_GOAL.md; team/PO acceptance pending |
| D-02 | Independent synthetic data rather than dependence on running Device/Gateway/Cloud services | Planning baseline consistent with accepted local-JSON proposal | Supports reproducible demonstrations and explicit course assumptions; live ingestion deferred | SPRINT_GOAL.md; revisit only through explicit scope change |
| D-03 | Coverage measured as PQC connection segments / all in-scope connection segments including unknown; zero records means unavailable | Prototype implementation choice by integrating AI under user-authorized construction; team/PO review pending | Including unknown prevents inflated coverage; alternative known-only denominator would hide uncertainty | S1-US-02; hand-worked fixture expectation: 5 / 8 = 62.5%; implementation checks recorded in VERIFICATION.md; human review pending |
| D-04 | Explicit historical demo clock pinned to snapshot time; optional current-time clock. Per-record age greater than 24 hours is stale. Overall precedence: suspected downgrade => red; otherwise empty/unknown/stale/future observations or future snapshot relative to selected clock => unknown; otherwise fallback => amber; otherwise green | Prototype implementation rule recorded before implementation; chosen by integrating AI, not teacher approval | Fixed clock makes demonstrations repeatable while identifying them as historical. Current-time mode reveals aging. Green describes reported segment migration only. Alternative live-only clock makes a fixed historical fixture stale immediately; an unexplained coverage-to-color threshold hides uncertainty | S1-US-04, S1-US-05; model and browser checks in VERIFICATION.md; team/PO review pending |
| D-05 | Existing prototype fallback logs as background rather than automatic HNDL evidence | Technical interpretation recorded from current goal and README; human domain review pending | Preconfigured symmetric keys differ from classical key exchange; synthetic exposure needs explicit assumptions | R-04; domain review before mapping prototype data |
| D-06 | Prepare local stories, then map them to the course Jira project | Initial boundary superseded by the user-confirmed Jira entry | Preserve local IDs and distinguish the Jira entry from prior build and meeting history | [Backlog mapping](BACKLOG.md); [SCRUM-10](https://tacczy.atlassian.net/browse/SCRUM-10) tracks team confirmation of estimates, roles and priorities |
| D-07 | Reject the entire invalid snapshot visibly, rather than silently dropping unsupported records | Prototype implementation choice by integrating AI under authorized construction | Prevents denominator changes and retained healthy summaries after bad input. Require synthetic schema v1, unique IDs, valid statuses/methods and observation times no later than snapshot time | S1-US-01, S1-US-02; schema/model checks passed; invalid-input UI reset observed; human review pending |
| D-08 | Record supplied membership separately from confirmed roles, contributions and review outcomes | User supplied the roster; evidence classification by integrating AI | Known members are recorded in TEAM_REVIEW.md. No member is assigned a role or credited with work by inference; AI review supports later human review | Team to confirm actual roles, opinions, decisions and sign-off; Jira/PO acceptance unchanged |
| D-09 | Allocate prospective responsibilities under user delegation, rather than reconstruct past contributions or member feedback | User explicitly delegated allocation after reporting that group review occurred without a saved record | Initial allocation superseded by D-10. Review participation and individual contributions remain separate | Actual review date, attendees, opinions and acceptance decision are unconfirmed. Planned later Scrum Master rotation is prospective, not completed |
| D-10 | Update the Sprint 1 work allocation | User supplied revised responsibilities | TEAM_REVIEW.md records the current allocation for Jira, documentation, submission coordination, UI, verification, video, report and slides | Confirm individual Jira assignees and any remaining Scrum role decisions with the team |

## Change record

| Event | Change | Evidence | Residual work at that stage |
| --- | --- | --- | --- |
| Initial planning draft | R-01 through R-08 and D-01 through D-06 documented by delegated AI author | User request, Sprint goal and this local file; parent integration review recorded in LLM_EVALUATION.md | Student ownership, PO feedback and implementation verification pending; all risks remain open |
| First build batch started | D-03/D-04 selected as explicit prototype rules; D-07 records rejection policy | User instruction to start construction; delegated model/UI task contracts; BUILD_PROMPTS.md | Model tests, integrated browser checks, student/PO review pending |
| First build batch integrated | Five stories implemented; parent independently observed 11/11 model checks and scoped browser walkthrough | VERIFICATION.md; AI-S1-002 in LLM_EVALUATION.md | All risks remain open for human review; mobile full-page screenshot capture failed; Jira entry and teacher acceptance pending |
| Roster received and material review requested | User supplied five members; R-09 and D-08 distinguish membership from process evidence | TEAM_REVIEW.md; AI-S1-004 in LLM_EVALUATION.md | Actual roles, meeting facts, individual opinions, Jira mapping and sign-off remain pending; no human-acceptance risk closed |
| Review clarification and forward allocation | User reports review held, original record not saved; delegated role allocation recorded as D-09 | Current project chat; TEAM_REVIEW.md | Confirm actual review date/attendees/findings and acknowledge forward roles; retrospective remains unconfirmed; no invented opinions or risk closure |
| Independent material review integrated | Reviewer reran 11/11 model tests, independently checked 8 = 5 + 2 + 1 and inspected executive/fallback screenshot-caption agreement; no actionable synthetic-scope defect found | TEAM_REVIEW.md; AI-S1-004 in LLM_EVALUATION.md | At that review, human evidence, Jira mapping, mobile validation and teacher/PO acceptance were still open |
| Jira entry confirmed | The user verified the saved Sprint Goal, ten mapped items and six dependencies | [Backlog mapping](BACKLOG.md); [SCRUM-11](https://tacczy.atlassian.net/browse/SCRUM-11) tracks risk and decision maintenance | R-07 traceability improved; earlier Jira activity, confirmed dates, estimates, ownership and actual meeting outcomes still require evidence. Risks remain open |

For a new decision, append ID, trigger, alternatives, chosen action, authority,
affected stories, verification and residual risk. Record proposals as proposals
until the named decision maker actually accepts them.

## First build mitigation evidence

The parent independently observed 11/11 model checks, passing model/app syntax
checks, HTTP 200 and the browser walkthrough in [VERIFICATION.md](VERIFICATION.md).
The build-records AI performed a separate source review of the model, fixture, UI
and startup explanation with no actionable domain/metric mismatch identified.

- R-01/R-03/R-04: fixture and UI distinguish expected/suspected fallback, model
  assumptions and mixed connection segments; explanations inspected in browser.
- R-02: default and edge-case counts, unknown denominator, empty coverage and
  filtered/global reconciliation exercised.
- R-05: independent static dashboard runs without protocol services; optional
  backend/security redesign stayed outside this increment.
- R-06: AI provenance and review recorded; an incorrect initial model-test search
  expectation was corrected, rather than reported as an implementation defect.
- R-07/R-09: the local-to-Jira mapping is now recorded. The user reports a
  group review was held without retained minutes. The date, actual attendees,
  feedback, acceptance and retrospective still need confirmation. D-09
  records proposed responsibilities for follow-up.
- R-08: stale/all-PQC and unknown/empty cases prevent all-clear under the rule;
  green wording is qualified. Mobile geometry was checked, but full-page mobile
  screenshot capture failed, leaving complete mobile visual validation open.

These checks mitigate known failure modes only. They do not close risks or prove
real monitoring, security assurance, human comprehension or teacher acceptance.
