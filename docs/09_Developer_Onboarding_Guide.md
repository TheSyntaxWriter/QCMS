# Developer Onboarding Guide

## Prerequisites

- Python compatible with Django 5.2.
- pip.
- Virtual environment support.
- Git.
- SQLite for local development.
- System dependencies for WeasyPrint if PDF export is tested locally.

## Local Setup

1. Clone or open the project.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Apply migrations:

```bash
python manage.py migrate
```

5. Create a superuser if needed:

```bash
python manage.py createsuperuser
```

6. Run development server:

```bash
python manage.py runserver
```

7. Open:

```text
http://127.0.0.1:8000/
```

## Key Files to Read First

1. `qcms/settings.py`
2. `backend/urls.py`
3. `backend/models.py`
4. `backend/views/common.py`
5. `backend/views/auth.py`
6. `backend/views/user_panel.py`
7. `backend/views/admin.py`
8. `backend/workflow_service.py`
9. `backend/permission_service.py`
10. `frontend/templates/admin_panel/admin_base.html`
11. `frontend/templates/user_panel/base_user.html`

## Development Structure

### Backend

| Path | Responsibility |
| --- | --- |
| `backend/models.py` | ORM models and domain schema. |
| `backend/urls.py` | Application route mapping. |
| `backend/views/auth.py` | Authentication views. |
| `backend/views/common.py` | Shared profile/redirect helpers. |
| `backend/views/admin.py` | Admin dashboard, CRUD, checklist builder, responses, logs, settings. |
| `backend/views/user_panel.py` | User/HOD/Management checklist, submissions, profile workflows. |
| `backend/views/management.py` | Management dashboard redirect. |
| `backend/workflow_service.py` | Response statuses and transitions. |
| `backend/permission_service.py` | Role permissions and response query scoping. |
| `backend/logging_service.py` | Activity log writer. |
| `backend/middleware.py` | Request tracking for logs. |
| `backend/tests.py` | Existing tests. |

### Frontend

| Path | Responsibility |
| --- | --- |
| `frontend/templates/login.html` | Login UI. |
| `frontend/templates/admin_panel/` | Admin page templates. |
| `frontend/templates/user_panel/` | User/HOD/Management templates. |
| `frontend/templates/shared/` | Shared checklist preview content. |
| `frontend/templates/admin_panel/partials/` | Shared table/sidebar partials. |
| `frontend/static/shared/` | Shared CSS/JS. |
| `frontend/static/admin_panel/` | Checklist/response JS and CSS. |
| `frontend/static/admin_users/` | User/master CRUD JS and CSS. |
| `frontend/static/user_panel/` | User page JS and CSS. |

## Running Tests

Run:

```bash
python manage.py test
```

Current tests cover:

- Access control.
- Role redirects.
- Checklist builder create/edit.
- Option validation.
- Checklist preview/PDF rendering.

## Development Workflow

Recommended workflow:

1. Create or update tests for behavior changes.
2. Update models/migrations if schema changes.
3. Keep permission logic in `permission_service.py`.
4. Keep status transition logic in `workflow_service.py`.
5. Keep views thin where possible.
6. Use templates for HTML escaping and avoid unsafe JS `innerHTML`.
7. Run tests.
8. Run `python manage.py check`.
9. For deployment-related work, run `python manage.py check --deploy`.

## Adding a New Checklist Question Type

Steps:

1. Add constant and choice to `ChecklistQuestion.QUESTION_TYPES`.
2. Update checklist builder JavaScript to render editor/preview control.
3. Update `checklist_fill.html` to render input control.
4. Update answer extraction in `_extract_answer` if needed.
5. Update validation rules if needed.
6. Add tests for builder validation and submission.

## Adding a New Response Status

Steps:

1. Add status to `ResponseStatus`.
2. Add it to `ResponseStatus.CHOICES`.
3. Update `STATUS_TRANSITIONS`.
4. Update action mapping if needed.
5. Update admin/user filters.
6. Update dashboard counts.
7. Update tests.

## Adding a New Role

Steps:

1. Add role to `UserProfile.ROLE_CHOICES`.
2. Add redirect behavior in `redirect_for_profile`.
3. Add sidebar/navigation behavior.
4. Add response scoping in `responses_for_profile`.
5. Add valid action ceiling in `ROLE_SCOPED_ACTIONS`.
6. Add role permission UI if needed.
7. Add access-control tests.

## Adding Admin Pages

Recommended steps:

1. Add view function.
2. Add route in `backend/urls.py`.
3. Add template under `frontend/templates/admin_panel/`.
4. Add static JS/CSS only if page-specific behavior is needed.
5. Add sidebar item in `_admin_sidebar_menu`.
6. Add tests for authentication and role access.

## Coding Conventions in This Project

- Views are function-based.
- Role checks are performed manually inside views.
- Templates extend `admin_base.html` or `base_user.html`.
- Page-specific JavaScript usually reads config from `window.*Config` or `json_script`.
- Server-side role and workflow validation should be treated as authoritative.

## Known Technical Debt

- Large `backend/views/admin.py` should be split.
- Legacy models remain.
- Some JS uses unsafe `innerHTML`.
- Some status names overlap old and new workflows.
- Development settings need production separation.
- Some generated files appear tracked in git.

## Recommended Refactor Targets

- Split `backend/views/admin.py` into:
  - `admin_dashboard.py`
  - `admin_users.py`
  - `admin_master_data.py`
  - `admin_checklists.py`
  - `admin_responses.py`
  - `admin_settings.py`
  - `admin_logs.py`
- Move checklist builder parsing/validation into a service.
- Move response action handling into a service.
- Add reusable decorators for role access.
- Add reusable upload validators.
- Introduce model/queryset methods for common scopes.
