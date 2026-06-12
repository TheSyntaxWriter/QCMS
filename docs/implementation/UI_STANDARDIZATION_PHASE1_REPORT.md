# UI Standardization Phase 1 Report

## Summary

UI Standardization Phase 1 was implemented on branch `codex/ui-standardization-phase1`. The change is presentation-only: it does not alter QCMS permissions, workflow transitions, approval behavior, database models, or business rules.

## Features Implemented

### 1. Notification Control naming

- Renamed the Admin sidebar item from `Notifications` to `Notification Control`.
- Renamed the Admin page heading to `Notification Control`.
- Updated the settings save action, success message, audit description, generated settings-change notification title, and notification message to use the same administrative name.
- Retained `Notifications` for the personal notification bell and drawer because those are user-facing notification consumption surfaces, not the Admin configuration surface.

### 2. Header profile identity

- Added a shared `header_identity.html` partial used by both Admin and User/HOD/Management base layouts.
- Displays the stored profile picture when available.
- Displays an initials avatar when no profile picture exists.
- Places the avatar before the welcome/username text.
- Links the avatar to the correct profile page for the authenticated role.
- Added accessible labels, keyboard focus styling, fixed dimensions, and responsive mobile behavior.
- On narrow mobile screens, the welcome text is hidden while the avatar and notification bell remain available.

### 3. Centralized cursor system

- Added one cursor policy to `frontend/static/shared/ui_system.css`.
- Standardized pointer cursors for buttons, links, selects, interactive controls, notification rows, selection items, and color controls.
- Standardized text cursors for editable text fields.
- Standardized `not-allowed` for disabled and ARIA-disabled controls.
- Removed all page-level and component-level `cursor:` declarations from templates and CSS files.
- Added the shared UI stylesheet to the standalone login and generic base templates so they use the same cursor policy.

### 4. Left-aligned table actions

- Strengthened the shared `.actions-column` and `.action-column` contract with consistent left alignment.
- Kept action groups as left-aligned flex containers with shared spacing.
- Added explicit action-column classes and action wrappers to:
  - Admin Users
  - Departments
  - Projects
  - Checklist lists
  - Response lists
  - Role permission controls
  - Checklist details controls
- Removed the Admin Users rule that centered the final table cell.

## Files Changed

### Shared UI

- `frontend/static/shared/ui_system.css`
- `frontend/static/shared/table_system.css`
- `frontend/static/shared/sidebar.css`
- `frontend/static/shared/notification_center.css`
- `frontend/templates/shared/header_identity.html`

### Base layouts and standalone pages

- `frontend/templates/admin_panel/admin_base.html`
- `frontend/templates/user_panel/base_user.html`
- `frontend/templates/base.html`
- `frontend/templates/login.html`

### Admin naming and tables

- `backend/notification_service.py`
- `backend/views/admin.py`
- `backend/views/notifications.py`
- `frontend/templates/admin_panel/admin_notification_settings.html`
- `frontend/templates/admin_panel/admin_users.html`
- `frontend/templates/admin_panel/admin_departments.html`
- `frontend/templates/admin_panel/admin_projects.html`
- `frontend/templates/admin_panel/admin_responses.html`
- `frontend/templates/admin_panel/checklist_create.html`
- `frontend/templates/admin_panel/partials/checklist_table.html`
- `frontend/templates/admin_panel/partials/response_table.html`

### Cursor cleanup

- `frontend/static/admin_dashboard/admin_dashboard.css`
- `frontend/static/admin_panel/checklist_response.css`
- `frontend/static/admin_users/admin_users.css`
- `frontend/static/user_panel/checklist_fill.css`
- `frontend/templates/admin_panel/admin_control_panel.html`
- `frontend/templates/admin_panel/admin_profile.html`
- `frontend/templates/user_panel/profile.html`

### Tests

- `backend/tests.py`

## Verification

### Django checks

```text
python manage.py check
System check identified no issues (0 silenced).
```

### Focused integration tests

```text
python manage.py test \
  backend.tests.NotificationCenterTests.test_authenticated_header_contains_notification_bell \
  backend.tests.NotificationCenterTests.test_admin_ui_uses_notification_control_name

Ran 2 tests - OK
```

### Full test suite

```text
python manage.py test
Ran 62 tests - OK
```

The tests verify the shared notification bell, initials avatar fallback, profile link accessibility label, Admin sidebar naming, page heading, and save-action naming.

## Compatibility and Risk Assessment

- **Database migrations:** None.
- **Business logic:** Unchanged.
- **Permissions:** Unchanged.
- **Workflow behavior:** Unchanged.
- **Responsive risk:** Low. Header identity uses fixed avatar dimensions and hides only the welcome text below 640 px.
- **CSS cascade risk:** Low to medium. Action alignment uses `!important` only on the semantic action-column contract to override known page-level table centering.
- **Profile data risk:** Low. Existing `UserProfile.profile_image` is reused; missing images fall back to initials without requiring data migration.
- **Browser preview note:** A live local preview could not be completed because the development server encountered a local SQLite disk I/O error when its context processor attempted database access. No preview user or database record was created. Django template integration tests and the full test suite passed.

## Out of Scope

- Card profile selection.
- Button profile selection.
- Icon library replacement.
- Universal table filtering, export, or page-size changes.
- Permission, approval, notification delivery, or workflow changes.
