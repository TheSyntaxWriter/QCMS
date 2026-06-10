# User Roles and Permissions

## Role Model

QCMS roles are stored on `UserProfile.role`, not directly on Django groups or permissions. The role values are:

- `User`
- `HOD`
- `Management`
- `Admin`

Django superusers are handled specially by redirect logic and are sent to Django's built-in `/admin/` site.

## Role Landing Pages

| Role | Landing Page |
| --- | --- |
| Admin | `/admin-panel/` |
| Management | `/dashboard/` |
| HOD | `/my-checklists/` |
| User | `/my-checklists/` |
| Django superuser | `/admin/` |

## Admin

Admins operate the QCMS administration panel.

Capabilities:

- View admin dashboard.
- Manage users.
- Manage departments.
- Manage projects.
- Manage checklists.
- Create/edit checklist definitions.
- Preview and export checklists as PDF.
- View all checklist responses.
- Approve/reject/toggle/delete responses subject to workflow rules.
- Configure response table columns/actions for roles.
- View activity logs.
- Configure branding and control panel settings.
- Access admin profile page.

Permission behavior:

- `get_role_permission_config('Admin')` returns all valid columns and all valid actions.
- Admin response actions still pass through workflow validation for status actions.
- Admin can edit responses according to `can_edit_response`, which returns true for Admin.

## User

Standard checklist submitter.

Capabilities:

- View assigned checklists.
- Preview assigned checklists.
- Download assigned checklist PDFs.
- Fill assigned checklists.
- Save response as WIP.
- Submit response for approval.
- View own submissions.
- Edit own WIP responses.
- Edit own rejected responses if workflow permits.
- Update profile image.
- Change password.

Scope:

- Checklist visibility is based on profile department and project/domain assignment.
- Response visibility is restricted to `submitted_by=request.user`.

Allowed action ceiling:

- `view`
- `edit`

## HOD

Department-level reviewer role.

Capabilities:

- View assigned/departmental checklists.
- View scoped responses.
- Approve or reject responses if allowed by role permission config and workflow state.
- View profile and change password/profile image.

Scope:

- Responses are filtered by profile department.
- If the HOD has a project, responses are also filtered by project and project domain.
- Checklists are filtered by department.

Allowed action ceiling:

- `view`
- `approve`
- `reject`

## Management

Management reviewer role with dashboard access.

Capabilities:

- View management dashboard.
- View checklist list.
- View scoped submissions.
- Approve or reject responses if allowed by role permission config and workflow state.
- View profile and change password/profile image.

Scope:

- If department is present, responses are filtered by department.
- If project is present, responses are filtered by project and domain.
- If no scoping data is present, response queryset returns none.
- Checklist list currently returns all checklists for Management.

Allowed action ceiling:

- `view`
- `approve`
- `reject`

## RolePermission Configuration

`RolePermission` allows Admins to configure:

- Visible response table columns.
- Allowed response actions.
- Selected projects.

Valid columns:

- `checklist_id`
- `checklist_name`
- `checklist_type`
- `submitted_by`
- `project`
- `department`
- `hod_name`
- `submission_datetime`
- `status`
- `last_updated_by`
- `last_updated`
- `actions`

Valid actions:

- `view`
- `edit`
- `approve`
- `reject`
- `delete`
- `toggle`

Role action ceilings:

| Role | Maximum Actions |
| --- | --- |
| Admin | `view`, `edit`, `approve`, `reject`, `delete`, `toggle` |
| Management | `view`, `approve`, `reject` |
| HOD | `view`, `approve`, `reject` |
| User | `view`, `edit` |

The role ceiling prevents configuration from granting actions outside the intended role boundary.

## Backend Permission Evaluation

The backend evaluates permissions in layers:

1. The user must be authenticated.
2. The user must have a `UserProfile`.
3. The view checks whether the role is allowed on that page.
4. `responses_for_profile` scopes visible response records.
5. `get_role_permission_config` loads visible columns and base actions.
6. `is_action_permitted_for_response` checks action-specific workflow/role rules.
7. `effective_allowed_actions_for_response` computes allowed actions per response.

## Important Permission Notes

- UI action visibility is not sufficient by itself; server-side checks in `permission_service.py` are the authoritative guard for response actions.
- `selected_projects` is currently stored on `RolePermission`, but the main response scoping service does not fully enforce it.
- Management checklist visibility is broader than User/HOD checklist visibility.
- The active profile flag exists, but most view checks rely on authentication and role rather than consistently checking `UserProfile.is_active`.

## Recommended Permission Improvements

- Enforce `UserProfile.is_active` consistently at login or middleware level.
- Enforce `RolePermission.selected_projects` or remove it from the UI/schema.
- Use Django groups/permissions or a policy layer if permission needs become more granular.
- Render action buttons from per-response effective actions, not only broad role actions.
- Add tests for every role/action/status combination.
