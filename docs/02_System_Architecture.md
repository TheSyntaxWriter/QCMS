# System Architecture

## Architectural Style

QCMS is a Django monolith with a traditional Model-Template-View structure:

- Models define the domain and persistence layer.
- Views handle request validation, role checks, ORM queries, business actions, and template rendering.
- Templates render HTML for the admin and user panels.
- Static JavaScript adds modals, AJAX form submissions, chart rendering, and checklist-builder behavior.
- Service modules centralize workflow, permissions, logging, and request tracking.

## Request Lifecycle

```text
Browser
  -> qcms.urls
  -> backend.urls
  -> backend.views.*
  -> backend.models / services
  -> frontend/templates
  -> frontend/static assets
  -> Browser
```

For POST/AJAX actions:

```text
Browser JS or HTML form
  -> Django URL route
  -> View role/profile validation
  -> Permission/workflow service validation
  -> ORM write
  -> ActivityLog write
  -> Redirect or JSON response
```

## Django Project Modules

### `qcms/settings.py`

Configures:

- Installed apps.
- Middleware.
- Template directories.
- SQLite database.
- Static and media paths.
- Login/logout URLs.
- Branding defaults.

Important middleware includes Django's default security/session/auth/CSRF middleware plus `backend.middleware.RequestTrackingMiddleware`.

### `qcms/urls.py`

Defines root URL routing:

- `/admin/` goes to Django admin.
- `/` includes `backend.urls`.
- Media files are served from `MEDIA_ROOT` in development.

### `qcms/context_processors.py`

Provides global branding values to templates:

- `PROJECT_DISPLAY_NAME`
- `PROJECT_SHORT_NAME`
- `GLOBAL_BRANDING`
- `GLOBAL_THEME`

It reads from `AppSettings.get_solo()`.

### `qcms/asgi.py` and `qcms/wsgi.py`

Standard Django ASGI/WSGI entry points for deployment.

## Backend Application Modules

### `backend/models.py`

Contains all application data models:

- Master data: `Project`, `Department`, `ChecklistType`.
- User metadata: `UserProfile`.
- Checklist templates: `ChecklistDefinition`, `ChecklistQuestion`.
- Checklist responses: `ChecklistResponse`, `ChecklistAnswer`.
- Legacy checklist models: `Checklist`, `Section`, `Question`.
- Permissions: `RolePermission`.
- Audit logging: `ActivityLog`.
- Branding/settings: `AppSettings`.

### `backend/urls.py`

Maps application URLs to view functions, including:

- Auth routes.
- User panel routes.
- Management route.
- Admin panel routes.
- Admin action endpoints.
- User response action endpoint.

### `backend/views/auth.py`

Handles:

- Home redirect.
- Login.
- Logout.
- Login success/failure audit logging.
- Safe `next` URL support through common helpers.

### `backend/views/common.py`

Shared helpers:

- `get_user_profile(user)`
- `redirect_for_profile(profile, user=None)`
- `safe_next_url(request)`

This module centralizes profile lookup and role-based landing behavior.

### `backend/views/user_panel.py`

Handles non-admin panel workflows:

- Sidebar menu construction.
- Checklist visibility by profile.
- My checklists list.
- My submissions list.
- Management dashboard page.
- User/admin profile editing shared implementation.
- Profile image crop/upload processing.
- Password change.
- Checklist fill and WIP/submission flow.
- User/HOD/Management response actions.
- User checklist preview and PDF export.

### `backend/views/admin.py`

Handles admin workflows:

- Admin sidebar.
- Admin dashboard counts/charts.
- User list/search/sort/chart page.
- Department management.
- Project management.
- Checklist list/filter page.
- Checklist builder context and save action.
- Checklist preview and PDF export.
- Response list/filter/chart page.
- Role permission save action.
- Response approve/reject/delete/toggle actions.
- Control panel settings.
- Activity log page.
- User, department, and project action endpoints.

This is currently the largest module and contains several distinct concerns.

### `backend/views/management.py`

Legacy/simple route that validates a Management user and redirects to the common dashboard.

### `backend/workflow_service.py`

Centralizes checklist response status definitions and transitions:

- `ResponseStatus`
- `STATUS_TRANSITIONS`
- `ACTION_TO_TARGET_STATUS`
- `WorkflowDecision`
- `evaluate_status_action`
- `can_edit_response`
- `can_submit_response`
- `can_approve_response`
- `can_reject_response`

### `backend/permission_service.py`

Centralizes response visibility and action permission logic:

- Valid response table columns.
- Valid response actions.
- Role-scoped action ceilings.
- Role permission config lookup.
- Response queryset scoping per profile.
- Backend-safe response action checks.

### `backend/logging_service.py`

Writes `ActivityLog` records and enriches them with:

- Current request IP.
- User agent.
- User profile role.
- Department.
- Project.

It uses a request context variable populated by middleware.

### `backend/middleware.py`

Defines `RequestTrackingMiddleware`, which stores the current request so `logging_service` can access request metadata during logging.

### `backend/admin.py`

Registers models in Django admin.

### `backend/tests.py`

Contains tests for:

- Admin access control.
- Dashboard access control.
- Home redirects.
- Checklist builder creation/editing.
- Option-based question validation.
- Checklist preview and PDF rendering.

## Frontend Architecture

### Template Areas

| Area | Path | Purpose |
| --- | --- | --- |
| Login | `frontend/templates/login.html` | Authentication form. |
| Base legacy | `frontend/templates/base.html` | Older generic base layout. |
| Admin base | `frontend/templates/admin_panel/admin_base.html` | Admin shell, sidebar, topbar, shared admin CSS. |
| User base | `frontend/templates/user_panel/base_user.html` | User/HOD/Management shell. |
| Admin pages | `frontend/templates/admin_panel/` | Dashboard, users, departments, projects, checklists, responses, logs, control panel, profile. |
| User pages | `frontend/templates/user_panel/` | My checklists, fill checklist, submissions, profile, dashboard. |
| Shared preview | `frontend/templates/shared/checklist_preview_content.html` | Checklist preview/PDF content. |
| Partials | `frontend/templates/admin_panel/partials/` | Shared response/checklist tables and sidebar. |

### Static Asset Areas

| Area | Path | Purpose |
| --- | --- | --- |
| Shared UI | `frontend/static/shared/` | Sidebar, table, and UI system styles/scripts. |
| Admin dashboard | `frontend/static/admin_dashboard/` | Dashboard CSS/JS charts. |
| Admin panel | `frontend/static/admin_panel/` | Checklist builder, responses, PDF/response CSS. |
| Admin users | `frontend/static/admin_users/` | User/department/project CRUD styles/scripts and charts. |
| User panel | `frontend/static/user_panel/` | Checklist fill CSS and submissions JS. |
| Images | `frontend/static/images/` | Default favicon and logo. |

## Data Flow Summary

### Login

1. User submits username/password.
2. Django `authenticate` validates credentials.
3. User is logged in and session key is cycled.
4. Login success or failure is written to `ActivityLog`.
5. User is redirected based on profile role.

### Checklist Definition

1. Admin opens checklist builder.
2. Builder JavaScript maintains a JSON state of sections/questions.
3. Admin submits checklist metadata and builder JSON to `admin_checklist_action`.
4. Server validates metadata, question types, required data, and options.
5. Server creates or updates `ChecklistDefinition`.
6. Server creates, updates, or deletes `ChecklistQuestion` rows.
7. Project and department many-to-many assignments are saved.

### Checklist Completion

1. User opens an assigned checklist.
2. Server builds sectioned question groups.
3. User saves as WIP or submits for approval.
4. Server validates required questions unless saving WIP.
5. Server creates or updates `ChecklistResponse`.
6. Server creates or updates `ChecklistAnswer` rows.
7. HOD is resolved from the user's department where available.

### Response Review

1. Response pages fetch responses scoped by role.
2. Role permissions determine visible columns and actions.
3. Workflow checks determine whether edit/approve/reject is valid.
4. Actions update response status and `updated_by`.

## Architectural Strengths

- Domain is mostly modeled with explicit Django models.
- Permission and workflow logic are partly centralized in services.
- Views use `select_related`/`prefetch_related` in several important places.
- Templates are organized by audience.
- Audit logging is present for major operations.
- Checklist builder uses structured JSON and server-side validation.

## Architectural Risks

- `backend/views/admin.py` has too many responsibilities.
- Production settings are not separated from development settings.
- Status model is evolving and currently has mixed old/new states.
- File upload handling needs stronger security boundaries.
- Some role permission data is stored but not fully enforced.
- Legacy models remain in the active model file.
