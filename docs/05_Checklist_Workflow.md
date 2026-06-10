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

The system resolves an HOD by finding the first active `UserProfile` where:

- `role='HOD'`
- `is_active=True`
- `department` matches submitter department.
- Linked Django user is active.

The matched HOD user ID is saved to `ChecklistResponse.hod`.

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
| `toggle` | `Pending` if current status is `Rejected`; otherwise `Rejected` |

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

- Role is `Admin`, `Management`, or `HOD`; and
- The status transition to `Approved` is allowed.

## Reject Rules

`can_reject_response` allows rejection when:

- Role is `Admin`, `Management`, or `HOD`; and
- The status transition to `Rejected` is allowed.

## Approval Process

The intended approval process is:

1. User creates a response.
2. User submits it for approval.
3. HOD or Management sees the response if it falls within their scope.
4. Reviewer chooses approve or reject.
5. Approved responses become final.
6. Rejected responses can return to the submitter for changes, depending on workflow action.
7. Admin can view and act across all responses.

## Current Workflow Caveats

- New submissions use `Pending for Approval`, but some dashboards count `Pending`.
- The status transition table still supports older `Pending` behavior.
- Rejected responses can transition to `Pending` or `WIP`, depending on action.
- The UI may show broad action buttons even when workflow later blocks the action.

## Recommended Workflow Enhancements

- Decide on one canonical submitted status: either `Pending` or `Pending for Approval`.
- Add explicit review history/comments.
- Add HOD-specific queues.
- Add notification events for submission, approval, rejection, and resubmission.
- Add status badges and timeline views.
- Add tests for all status transitions and role/action combinations.
