# Checklist Workflow

## Checklist Lifecycle

```text
Admin creates checklist type
  -> Admin creates checklist definition
  -> Admin adds sections/questions
  -> Admin assigns projects/departments
  -> User/HOD/Management sees eligible checklist
  -> User fills checklist
  -> User saves WIP or submits for approval
  -> HOD/Management/Admin reviews response
  -> Response is approved or rejected
  -> Rejected response may be edited/reopened depending on workflow
```

## Checklist Template Creation

Checklist templates are created through the Admin checklist builder.

Admin provides:

- Checklist ID.
- Checklist name.
- Checklist type.
- Eligible projects.
- Eligible departments.
- One or more sections.
- One or more questions per section.

Question properties:

- Text.
- Type.
- Options for option-based types.
- Required flag.
- Display order.
- Section title.

Option-based types:

- Multiple choice.
- Checkbox.
- Dropdown.

These require at least one option.

## Active Question Types

| Type | Use |
| --- | --- |
| `short_text` | Single-line text answer. |
| `long_text` | Multi-line text answer. |
| `multiple_choice` | One radio-style choice. |
| `checkbox` | Multiple choices. |
| `dropdown` | One select-menu choice. |
| `file_upload` | Uploaded file answer. |
| `yes_no` | Yes/No radio choice. |
| `date` | Date input. |

## Checklist Assignment Logic

### User

A normal user's checklist list is filtered by:

- User's department.
- User's project.
- User's project domain.

The checklist must match the user's department and either the user's specific project or project domain.

### HOD

HOD checklist list is filtered by:

- HOD's department.

### Management

Management checklist list currently returns all checklist definitions.

## Filling a Checklist

Users open `/my-checklists/<checklist_id>/fill/`.

Server behavior:

1. Confirms authentication.
2. Confirms role is `User`, `HOD`, or `Management`.
3. Fetches only checklists visible to the user's profile.
4. Loads checklist questions.
5. Groups questions by `section`.
6. If editing a WIP response, preloads existing answers.
7. Renders the fill form.

## Saving WIP

When the user clicks "Save as WIP":

1. Form sends `workflow_action=save_wip`.
2. Target status becomes `WIP`.
3. Required question validation is skipped.
4. A `ChecklistResponse` is created or updated.
5. `ChecklistAnswer` rows are created or updated.
6. Activity log records `Checklist WIP Saved`.
7. User is redirected to My Submissions.

WIP responses can be edited by their owner.

## Submitting for Approval

When the user clicks "Submit for Approval":

1. Form sends `workflow_action=submit`.
2. Target status becomes `Pending for Approval`.
3. Required questions are validated.
4. Server creates or updates the response.
5. HOD is resolved by department.
6. Answers are saved.
7. Activity log records `Checklist Submitted`.
8. User is redirected to My Submissions.

## HOD Resolution

The submitter's active `UserProfile.assigned_hod` is the mandatory primary approver and is copied to `ChecklistResponse.hod` at submission. Existing records remain compatible through a department-based legacy fallback when no assigned HOD exists. Management and Admin can approve or reject as explicit override authorities; Management is not a required approval stage.

## Response Statuses

Defined statuses:

- `WIP`
- `Pending for Approval`
- `Pending`
- `Approved`
- `Rejected`

## Status Transitions

| Current Status | Allowed Next Statuses |
| --- | --- |
| `WIP` | `Pending for Approval` |
| `Pending for Approval` | `Approved`, `Rejected`, `WIP` |
| `Pending` | `Approved`, `Rejected` |
| `Approved` | None |
| `Rejected` | `Pending`, `WIP` |

## Action Mapping

| Action | Target Status |
| --- | --- |
| `approve` | `Approved` |
| `reject` | `Rejected` |

## Edit Rules

`can_edit_response` allows editing when:

- Role is `Admin`; or
- The user owns the response and status is `WIP` or `Rejected`.

## Submit Rules

`can_submit_response` allows submit when:

- Role is `Admin`; or
- The user owns the response and status is `WIP` or `Rejected`.

## Approve Rules

`can_approve_response` allows approval when:

- Role is `Admin` or `Management`; or the actor is the response owner's assigned HOD; and
- The status transition to `Approved` is allowed.

## Reject Rules

`can_reject_response` allows rejection when:

- Role is `Admin` or `Management`; or the actor is the response owner's assigned HOD; and
- The status transition to `Rejected` is allowed.

## Approval Process

The intended approval process is:

1. User creates a response.
2. User submits it for approval.
3. The assigned HOD receives the approval request and is the normal approver.
4. The HOD approves with an optional comment or rejects with a mandatory reason.
5. Approved responses become final.
6. Rejected responses can return to the submitter for changes, depending on workflow action.
7. Management and Admin can perform documented override approve/reject actions.
8. Every decision is stored in append-only `ResponseDecision` history and is visible to the owner.
9. In-app notifications inform the owner and relevant reviewer of workflow events.

## Current Workflow Caveats

- New submissions use `Pending for Approval`; legacy `Pending` remains supported for existing data.
- Dashboards count both submitted statuses as active pending work and display WIP separately.
- Rejected owners edit/resubmit explicitly; response Toggle actions have been removed.
- UI actions are generated per response from backend permission and workflow checks.

## Recommended Workflow Enhancements

- Decide on one canonical submitted status: either `Pending` or `Pending for Approval`.
- Consider a dedicated assigned-HOD queue and aging indicators.
- Normalize legacy `Pending` after a controlled data migration.
- Add SLA/escalation only after business rules are approved.
- Add status badges and timeline views.
- Add tests for all status transitions and role/action combinations.
