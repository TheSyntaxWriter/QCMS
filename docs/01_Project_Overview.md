# QCMS Project Overview

## Purpose

QCMS is a Django-based Quality Control Management System for creating, assigning, completing, reviewing, and auditing operational checklists. It is built as a server-rendered web application with Django templates, Django ORM models, role-based navigation, workflow status handling, file uploads, PDF export, global branding settings, and audit logging.

## Primary Capabilities

- User authentication and role-based landing pages.
- Master data management for departments, projects, users, and checklist types.
- Checklist builder with sections, questions, question types, required flags, and project/department assignment.
- Checklist preview and PDF export.
- Checklist completion by eligible users.
- Work-in-progress saving and submission for approval.
- Response review by HOD, Management, and Admin roles.
- Configurable response table columns and actions per role.
- Admin dashboard charts and summary counts.
- Activity logging for key authentication, profile, checklist, response, permission, and master-data actions.
- Admin control panel for app name, theme color, font, logo, and favicon.

## Technology Stack

- Backend framework: Django 5.2.5.
- Database: SQLite in the current local configuration.
- Frontend: Django templates, plain CSS, and vanilla JavaScript.
- Charts: Chart.js loaded from CDN in dashboard/user pages.
- PDF generation: WeasyPrint.
- Image processing: Pillow.
- Static assets: `frontend/static`.
- Templates: `frontend/templates`.
- Uploads: `media`.

## High-Level User Journey

1. A visitor opens `/`.
2. Anonymous users are redirected to `/login/`.
3. After successful login, the system reads `UserProfile.role`.
4. Admins are sent to the admin dashboard.
5. Management users are sent to the management dashboard.
6. Users and HODs are sent to their checklist list.
7. Admins define checklist templates and assign them to departments/projects.
8. Users complete assigned checklists.
9. Responses are reviewed through role-scoped response pages.
10. Important actions are recorded in `ActivityLog`.

## Project Structure

```text
qcms_webapp/
  manage.py
  requirements.txt
  db.sqlite3
  qcms/
  backend/
  frontend/
  media/
  docs/
```

## Folder Purpose

| Path | Purpose |
| --- | --- |
| `manage.py` | Django command entry point. |
| `requirements.txt` | Python dependency list. |
| `qcms/` | Django project configuration, root URLs, ASGI/WSGI, context processors. |
| `backend/` | Main Django application: models, views, services, middleware, tests, migrations. |
| `backend/views/` | View modules split by area: authentication, common helpers, admin, user panel, management. |
| `frontend/templates/` | Server-rendered HTML templates. |
| `frontend/static/` | CSS, JavaScript, images, shared UI assets. |
| `media/` | Uploaded profile images, checklist answer files, and branding images. |
| `docs/` | Project documentation. |

## Application Type

QCMS is a monolithic Django application rather than a separated API plus SPA. Most pages are rendered on the server and enhanced with page-specific JavaScript for modals, checklist builder interactions, charts, filtering, and AJAX actions.

## Key Domain Terms

| Term | Meaning |
| --- | --- |
| Project | A business/project unit, with a code, name, and domain. |
| Department | Organizational department. |
| UserProfile | Role and organizational metadata attached to Django's built-in `User`. |
| ChecklistDefinition | Checklist template/header created by Admin. |
| ChecklistQuestion | A question inside a checklist template. |
| ChecklistResponse | A user's submitted or in-progress checklist instance. |
| ChecklistAnswer | A response answer for a specific question. |
| RolePermission | Admin-configurable response table/action permission settings. |
| ActivityLog | Audit record for important system activity. |
| AppSettings | Singleton-style global branding and theme settings. |

## Current State Notes

- The active checklist system uses `ChecklistDefinition` and `ChecklistQuestion`.
- Legacy models `Checklist`, `Section`, and `Question` still exist but are not used by the current builder workflow.
- Status handling includes both older statuses (`Pending`, `Approved`, `Rejected`) and newer workflow statuses (`WIP`, `Pending for Approval`).
- The local settings are development-oriented and require production hardening before deployment.
