# Sprint 2 Jira upload record

Date: 13 November 2026. Project: UniOulu Group 22 (`SCRUM`).

## Verified final state

The Edge backlog was reloaded after creation and displayed **15 of 15 work items**
in existing **SCRUM Sprint 2**, sprint ID **3**. Sprint 1 retained its ten
existing items. The corrected Sprint goal was saved and visible after reload.

All nine stories and six process tasks have descriptions and acceptance
criteria from the corrected local backlog. Final task-list readback confirmed
**8 In Review, 4 In Progress and 3 To Do**, with no items marked Done.
Priorities were eight High and seven Medium. All fifteen remain unassigned;
estimates and Sprint dates were left blank. The Sprint remains unstarted.
These are verified Jira changes, separate from teacher/PO acceptance and
course submission.

[Open the backlog](https://tacczy.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog).
[Final board screenshot](evidence/jira-sprint2-2026-11-13.jpg) shows the Sprint
and visible rows; the lower rows were also checked in the page task list.

## Issue mapping

| Local ID | Jira work item | Verified workflow state, 13 November 2026 |
| --- | --- | --- |
| S2-US-06 | [SCRUM-15](https://tacczy.atlassian.net/browse/SCRUM-15) | In Review |
| S2-US-01 | [SCRUM-16](https://tacczy.atlassian.net/browse/SCRUM-16) | In Review |
| S2-US-07 | [SCRUM-17](https://tacczy.atlassian.net/browse/SCRUM-17) | In Review |
| S2-US-08 | [SCRUM-18](https://tacczy.atlassian.net/browse/SCRUM-18) | In Review |
| S2-US-09 | [SCRUM-19](https://tacczy.atlassian.net/browse/SCRUM-19) | In Review |
| S2-US-02 | [SCRUM-20](https://tacczy.atlassian.net/browse/SCRUM-20) | In Review |
| S2-US-03 | [SCRUM-21](https://tacczy.atlassian.net/browse/SCRUM-21) | To Do |
| S2-US-04 | [SCRUM-22](https://tacczy.atlassian.net/browse/SCRUM-22) | In Review |
| S2-US-05 | [SCRUM-23](https://tacczy.atlassian.net/browse/SCRUM-23) | In Progress |
| S2-T-01 | [SCRUM-24](https://tacczy.atlassian.net/browse/SCRUM-24) | In Progress |
| S2-T-02 | [SCRUM-25](https://tacczy.atlassian.net/browse/SCRUM-25) | In Progress |
| S2-T-03 | [SCRUM-26](https://tacczy.atlassian.net/browse/SCRUM-26) | In Review |
| S2-T-04 | [SCRUM-27](https://tacczy.atlassian.net/browse/SCRUM-27) | To Do |
| S2-T-05 | [SCRUM-28](https://tacczy.atlassian.net/browse/SCRUM-28) | To Do |
| S2-T-06 | [SCRUM-29](https://tacczy.atlassian.net/browse/SCRUM-29) | In Progress |

## Verified dependencies

Each row is a directed **blocks** link, read back after saving in Jira.
The ten links match the backlog's direct product dependencies. The graph has
no duplicate edges or cycles. Jira also displayed the reciprocal **is blocked
by** links on SCRUM-17 for SCRUM-15 and SCRUM-16. Dependencies express delivery
order; an In Review prerequisite does not imply accepted completion.

| Predecessor | Blocks |
| --- | --- |
| SCRUM-15 / S2-US-06 | SCRUM-17, SCRUM-18, SCRUM-19, SCRUM-20 |
| SCRUM-16 / S2-US-01 | SCRUM-17, SCRUM-20 |
| SCRUM-17 / S2-US-07 | SCRUM-18, SCRUM-19 |
| SCRUM-20 / S2-US-02 | SCRUM-18, SCRUM-21 |

All fifteen descriptions retain the local backlog ID, acceptance criteria and
implementation evidence. The five Rovo-created stories SCRUM-19 through
SCRUM-23 initially had an encoded line break appended to the GitHub URL. Each
description was restored from the prepared backlog source, saved and read back:
one local-ID marker, one acceptance-criteria section and the exact implementation
link below. SCRUM-20's editor briefly appended a second description; this was
detected and replaced before saving.

[Implementation commit](https://github.com/IQBoostPlus/pqcbridge-legacy-edge-cloud/commit/7f14cddc35f0ed555fd86ab58ed3ce07b8abed99).
This check verifies the saved hyperlink target and evidence mapping; it is not
a fresh product test or a new verification of GitHub publication.

## Method and recovery

The first four stories were created through the Jira form. The remaining
eleven were created through Jira Rovo after previewing all supplied fields.
A file-import attempt was blocked by the extension's local-file permission;
no permission or security setting was changed. The Jira creation callback
reported an invocation-format error after the eleven-item success message.
No retry of creation was made: the board was refreshed and all fifteen unique
items were verified instead, avoiding duplicates.

Final status and dependency edits were made through the Jira interface and
checked from the resulting task lists. A dropdown initially intercepted a
save click and selected an extra target; that target was removed, the editor
was cancelled and the correct two-target relationship was subsequently saved
and verified. No incorrect link was saved. A Sprint 1 date dialog opened while
preparing the screenshot was cancelled without changes. No manual upload or
browser security-setting change was required.

Remaining work is acknowledged roles/estimates, formal Sprint/review dates,
actual participant/process observations, teacher/PO feedback and course
artifacts/submission. Future retrospective action tickets require actual
agreed actions; the six process tasks above are not evidence that those
meetings or submissions have occurred.
