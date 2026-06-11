# Approval Comments Fix Report

## Scope

Resolved the two High-severity findings from the approval-comments review:

1. Response decision history was mutable.
2. Rejection reasons were enforced only in workflow views.

No unrelated workflow, permission, status, or UI behavior was changed.

## Append-Only History Fixes

- Existing `ResponseDecision` instances now reject subsequent `save()` calls.
- Instance and queryset deletion attempts now raise `ValidationError`.
- Queryset updates are blocked to prevent bulk modification.
- `bulk_create()` validates every decision before insertion.
- The relationship from `ResponseDecision` to `ChecklistResponse` now uses `PROTECT`, preventing parent-response deletion from cascading into audit-history deletion.
- The Admin response-delete endpoint returns a controlled error when decision history exists.
- Django Admin exposes `ResponseDecision` as a view-only audit record:
  - Add disabled.
  - Change disabled.
  - Delete disabled.
  - All fields read-only.

Existing decision records are preserved unchanged.

## Rejection Validation Fixes

- `ResponseDecision.clean()` requires a nonblank, non-whitespace comment when `action="reject"`.
- `ResponseDecision.save()` calls `full_clean()` for every new record.
- The custom manager validates objects passed through `bulk_create()`.
- Existing view-level rejection validation remains in place for immediate API feedback.
- Approval comments remain optional.

## Migration

- Added `backend/migrations/0014_protect_response_decision_history.py`.
- Changes only the decision-to-response foreign key from `CASCADE` to `PROTECT`.
- Does not rewrite or delete existing decision history.
- A pre-existing `AppSettings.web_app_name` migration-state difference was excluded because it is unrelated to these review fixes.

## Tests Added

- Rejecting without a reason fails direct model creation.
- Existing decisions cannot be modified through instance or queryset APIs.
- Decisions cannot be deleted through instance or queryset APIs.
- Responses with decision history cannot be deleted through the Admin response endpoint.
- Django Admin add/change/delete permissions are disabled for decision records.

## Verification

- `python manage.py makemigrations` - generated migration `0014`; unrelated AppSettings operation removed.
- `python manage.py migrate` - migration `0014_protect_response_decision_history` applied successfully.
- `python manage.py check` - no issues identified.
- `python manage.py test backend.tests.WorkflowPhase1Tests` - 18 tests passed.
- `python manage.py test` - 33 tests passed.

## Files Changed for These Fixes

- `backend/models.py`
- `backend/admin.py`
- `backend/views/admin.py`
- `backend/tests.py`
- `backend/migrations/0014_protect_response_decision_history.py`
- `APPROVAL_COMMENTS_FIX_REPORT.md`
