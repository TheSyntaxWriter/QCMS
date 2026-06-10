# URL and Navigation Flow

## Root Routing

`qcms/urls.py` routes:

| URL | Destination |
| --- | --- |
| `/admin/` | Django built-in admin site. |
| `/` | Includes `backend.urls`. |
| `/media/...` | Development media serving. |

## Application Routes

All main application routes are defined in `backend/urls.py`.

## Authentication Routes

| URL | Name | View | Purpose |
| --- | --- | --- | --- |
| `/` | `home` | `views.home` | Role-based landing redirect. |
| `/login/` | `login` | `views.user_login` | Login form and authentication. |
| `/logout/` | `logout` | `views.user_logout` | Logout and redirect to login. |

## User/HOD/Management Routes

| URL | Name | Purpose |
| --- | --- | --- |
| `/my-checklists/` | `my_checklists` | List visible checklists. |
| `/my-checklists/<id>/view/` | `user_checklist_preview` | Preview visible checklist. |
| `/my-checklists/<id>/pdf/` | `user_checklist_pdf` | Download checklist PDF. |
| `/my-checklists/<id>/fill/` | `user_checklist_fill` | Fill or edit a checklist response. |
| `/my-submissions/` | `my_submissions` | View scoped submissions. |
| `/my-submissions/action/` | `user_submission_action` | AJAX view/approve/reject action endpoint. |
| `/dashboard/` | `dashboard` | Management dashboard. |
| `/user/profile/` | `user_profile` | User/HOD/Management profile page. |
| `/management-dashboard/` | `management_dashboard` | Legacy management route redirecting to dashboard. |

## Admin Page Routes

| URL | Name | Purpose |
| --- | --- | --- |
| `/admin-panel/` | `admin_dashboard` | Admin dashboard. |
| `/admin-panel/users/` | `admin_users` | User management page. |
| `/admin-panel/departments/` | `admin_departments` | Department management page. |
| `/admin-panel/projects/` | `admin_projects` | Project management page. |
| `/admin-panel/checklists/` | `admin_checklists` | Checklist management page. |
| `/admin-panel/checklists/create/` | `admin_checklist_create` | Checklist builder create page. |
| `/admin-panel/checklists/<id>/edit/` | `admin_checklist_edit` | Checklist builder edit page. |
| `/admin-panel/checklists/<id>/view/` | `admin_checklist_view` | Checklist preview page. |
| `/admin-panel/checklists/<id>/pdf/` | `admin_checklist_pdf` | Checklist PDF export. |
| `/admin-panel/responses/` | `admin_responses` | Response management and permissions. |
| `/admin-panel/control-panel/` | `admin_control_panel` | Branding/theme control panel. |
| `/admin-panel/logs/` | `admin_logs` | Activity log page. |
| `/admin-panel/profile/` | `admin_profile` | Admin profile page. |

## Admin Action Routes

| URL | Name | Purpose |
| --- | --- | --- |
| `/admin-create/` | `admin_master_create` | Create users, departments, projects. |
| `/admin-master-create/` | `admin_create` | Legacy alias for create behavior. |
| `/admin-user-action/` | `admin_user_action` | User view/edit/delete/toggle actions. |
| `/admin-department-action/` | `admin_department_action` | Department edit/delete actions. |
| `/admin-project-action/` | `admin_project_action` | Project edit/delete actions. |
| `/admin-checklist-action/` | `admin_checklist_action` | Checklist create/edit/delete/toggle actions. |
| `/admin-response-action/` | `admin_response_action` | Response view/delete/toggle/approve/reject and permission save actions. |

## Navigation by Role

### Admin Sidebar

Admin sidebar items:

- Dashboard
- Checklist
- Response
- User
- Department
- Project
- Control Panel
- Logs
- Profile

### User Sidebar

User sidebar items:

- Checklist
- Response
- Profile

### HOD Sidebar

HOD uses the same base user sidebar:

- Checklist
- Response
- Profile

### Management Sidebar

Management sidebar includes:

- Dashboard
- Checklist
- Response
- Profile

## Main Navigation Flows

### Login Flow

```text
/login/
  -> authenticate
  -> role lookup
  -> Admin: /admin-panel/
  -> Management: /dashboard/
  -> User/HOD: /my-checklists/
```

### Admin Checklist Builder Flow

```text
/admin-panel/checklists/
  -> /admin-panel/checklists/create/
  -> JavaScript builder edits local JSON state
  -> POST /admin-checklist-action/
  -> redirect /admin-panel/checklists/
```

### User Checklist Fill Flow

```text
/my-checklists/
  -> /my-checklists/<id>/fill/
  -> save WIP or submit
  -> /my-submissions/
```

### Response Review Flow

```text
/admin-panel/responses/ or /my-submissions/
  -> View details through action endpoint
  -> Approve/reject/toggle/delete through POST action endpoint
  -> status updated
  -> page reload
```

### Profile Flow

```text
/user/profile/ or /admin-panel/profile/
  -> update cropped profile image
  -> or change password
  -> redirect back to profile
```

## Template Mapping

| View Area | Template |
| --- | --- |
| Login | `login.html` |
| Admin base | `admin_panel/admin_base.html` |
| User base | `user_panel/base_user.html` |
| Admin dashboard | `admin_panel/admin_dashboard.html` |
| Admin users | `admin_panel/admin_users.html` |
| Admin departments | `admin_panel/admin_departments.html` |
| Admin projects | `admin_panel/admin_projects.html` |
| Admin checklists | `admin_panel/admin_checklists.html` |
| Checklist builder | `admin_panel/checklist_create.html` |
| Checklist preview | `admin_panel/checklist_view.html`, `user_panel/checklist_view.html` |
| Admin responses | `admin_panel/admin_responses.html` |
| User submissions | `user_panel/my_submissions.html` |
| Checklist fill | `user_panel/checklist_fill.html` |
| Profiles | `admin_panel/admin_profile.html`, `user_panel/profile.html` |
| Logs | `admin_panel/admin_logs.html` |
| Control panel | `admin_panel/admin_control_panel.html` |

## Navigation Recommendations

- Add breadcrumb trails to deep admin pages.
- Make response action errors visible in the UI instead of silently reloading.
- Split legacy aliases from active routes once consumers are migrated.
- Add direct HOD review queue routes if HOD approval is a core process.
- Add consistent empty states and permission-denied pages.
