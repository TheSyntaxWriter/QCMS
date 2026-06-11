# Approval Comments Implementation Report

## Summary

Implemented approval comments and mandatory rejection reasons without changing the existing response status values or role authorization model. Decisions are stored as append-only history records so existing responses remain valid and repeated review cycles retain every recorded comment.

## Features Implemented

- Added `ResponseDecision` history records for approve and reject actions.
- Required a non-blank rejection reason in both HOD/Management and Admin action endpoints.
- Allowed optional approval comments for HOD, Management, and Admin actions.
- Stored the decision actor, actor role, override flag, comment, and timestamp.
- Kept HOD decisions restricted to the response's assigned HOD.
- Kept Management and Admin decisions as override actions under their existing permissions.
- Exposed decision history only through existing role-scoped response detail endpoints.
- Ensured checklist owners always retain the View action for their own submissions.
- Displayed complete approval and rejection history in response details using text-only DOM rendering.
- Added approve/reject dialogs with required-reason feedback for rejection.
- Removed the response Toggle action from templates, JavaScript, permission configuration, policy checks, and workflow action evaluation.
- Left-aligned response action controls for Admin, User, HOD, and Management tables.

## Migration

- `backend/migrations/0013_responsedecision.py`
  - Creates the `ResponseDecision` table.
  - Uses a nullable actor reference so user deletion does not remove decision history.
  - Cascades decision history when its parent response is deleted.
  - Existing checklist responses require no data migration and remain compatible.

## Files Changed

- `backend/models.py`
- `backend/admin.py`
- `backend/permission_service.py`
- `backend/workflow_service.py`
- `backend/views/admin.py`
- `backend/views/user_panel.py`
- `backend/tests.py`
- `backend/migrations/0013_responsedecision.py`
- `frontend/templates/admin_panel/admin_responses.html`
- `frontend/templates/admin_panel/partials/response_table.html`
- `frontend/templates/user_panel/my_submissions.html`
- `frontend/static/admin_panel/admin_responses.js`
- `frontend/static/user_panel/my_submissions.js`
- `frontend/static/admin_panel/checklist_response.css`
- `frontend/static/shared/table_system.css`

## Tests Added

- HOD rejection with a reason succeeds and records history.
- HOD rejection without a reason fails without changing response status.
- HOD approval with a comment records history.
- Management override with a comment records override history.
- Admin override with a comment records override history.
- Checklist owners can retrieve and open all decision comments.
- Response Toggle is absent from the UI and rejected by the backend.

## Verification Executed

- `python manage.py makemigrations` - generated migration `0013`.
- `python manage.py migrate` - migration applied successfully.
- `python manage.py check` - no issues identified.
- `python manage.py test backend.tests.WorkflowPhase1Tests` - 14 tests passed.
- `python manage.py test` - 29 tests passed.
- `node --check frontend/static/admin_panel/admin_responses.js` - passed.
- `node --check frontend/static/user_panel/my_submissions.js` - passed.

## Risks Identified

- Historic responses have no decision-history rows because prior comments were not collected; the UI displays an explicit empty-history message.
- Existing role-permission JSON may contain the retired `toggle` value. Runtime normalization now drops it without requiring a destructive data migration.
- The project has a pre-existing migration-state difference for `AppSettings.web_app_name`. It was deliberately excluded from migration `0013` because it is unrelated to this implementation.
- SQLite migration initially encountered a workspace disk I/O restriction; rerunning with appropriate filesystem access completed successfully.
