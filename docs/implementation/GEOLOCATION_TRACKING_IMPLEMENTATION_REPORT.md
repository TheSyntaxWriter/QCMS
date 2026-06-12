# Geolocation Tracking Implementation Report

## Summary

Implemented optional checklist-submission geolocation tracking based on `GEOLOCATION_RISK_ASSESSMENT.md`.

The feature is disabled by default and can be enabled from the Admin Control Panel. Location is requested once when the user submits a checklist for approval. Saving a WIP draft never requests or stores location information.

## Features Implemented

- Added **Enable Geolocation Tracking** to Admin Security Settings.
- Default state is disabled for new and existing installations.
- Added one-shot browser geolocation using `navigator.geolocation.getCurrentPosition()`.
- Capture occurs only for `Submit for Approval`.
- WIP saves bypass geolocation completely.
- Permission denial, browser failure, timeout, or unsupported browsers do not block submission.
- Added nullable response fields:
  - `latitude`
  - `longitude`
  - `accuracy`
  - `submission_ip`
- Added server-side coordinate parsing and range validation.
- `submission_ip` uses the server-observed `REMOTE_ADDR`, not a browser-controlled hidden field or untrusted forwarding header.
- Added location information to response details for:
  - Admin
  - HOD
  - User/checklist owner
- Added a safe **Open in Google Maps** link when valid coordinates exist.
- Existing responses display `Coordinates not captured` and remain fully compatible.

## Browser Behavior

- Location is requested only after the user initiates final submission.
- High accuracy is requested with a 10-second timeout and a maximum cached-position age of 60 seconds.
- The form continues submitting if permission is denied or location cannot be obtained.
- No continuous or background tracking is used.

## Migration

- Added `backend/migrations/0015_checklistresponse_geolocation.py`.
- Adds four nullable columns to `ChecklistResponse`.
- No data migration or default backfill is required.
- The unrelated pre-existing `AppSettings.web_app_name` migration drift was excluded from migration `0015`.

## Tests Added

- Geolocation is disabled by default.
- Admin can enable geolocation tracking.
- Enabled Submit stores coordinates, accuracy, and server-observed IP.
- Submission succeeds with null coordinates when permission is denied.
- WIP never stores location or submission IP.
- Invalid or out-of-range coordinates are not stored.
- Location data is available through User, HOD, and Admin response detail endpoints.

## Verification

- `python manage.py makemigrations` - migration generated and scoped to geolocation fields.
- `python manage.py migrate` - migration `0015_checklistresponse_geolocation` applied successfully.
- `python manage.py check` - no issues identified.
- Focused workflow suite - 25 tests passed.
- `python manage.py test` - 40 tests passed.
- JavaScript syntax checks passed for all changed scripts.
- `git diff --check` passed with line-ending notices only.

## Files Changed

- `backend/models.py`
- `backend/views/admin.py`
- `backend/views/user_panel.py`
- `backend/tests.py`
- `backend/migrations/0015_checklistresponse_geolocation.py`
- `frontend/templates/admin_panel/admin_control_panel.html`
- `frontend/templates/user_panel/checklist_fill.html`
- `frontend/static/user_panel/checklist_fill.js`
- `frontend/static/user_panel/checklist_fill.css`
- `frontend/static/admin_panel/admin_responses.js`
- `frontend/static/user_panel/my_submissions.js`
- `GEOLOCATION_TRACKING_IMPLEMENTATION_REPORT.md`

## Deployment Notes

- Browser geolocation requires HTTPS in production.
- Reverse-proxy deployments will record the proxy address in `submission_ip` until a trusted-proxy IP extraction policy is explicitly configured.
- Coordinates are client-reported audit context and must not be treated as proof of physical presence or user identity.
