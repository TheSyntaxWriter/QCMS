# Admin Guide

## Admin Access

Admins log in through `/login/`. After authentication, users with `UserProfile.role = Admin` are redirected to `/admin-panel/`.

Admins should use the QCMS admin panel for application management. Django's built-in `/admin/` is primarily for superusers and direct database administration.

## Dashboard

URL: `/admin-panel/`

The dashboard shows:

- Total users.
- Total checklists.
- Total departments.
- Total projects.
- Total submitted checklists.
- Pending, approved, and rejected counts.
- User active/inactive chart.
- Checklist active/inactive chart.
- Department/project user distribution charts.
- Recent transactions.

## User Management

URL: `/admin-panel/users/`

Admins can:

- Search users.
- Filter by department, project, and active status.
- Sort table columns.
- Add new users.
- Edit existing users.
- Change role, department, and project.
- Toggle active status.
- Delete users.

When adding a user, required data includes:

- Username.
- Password.
- Email.
- Role.

Optional data:

- First name.
- Last name.
- Department.
- Project.

## Department Management

URL: `/admin-panel/departments/`

Admins can:

- View departments.
- Add departments.
- Edit department code/name/status.
- Delete departments.

Department fields:

- Code.
- Name.
- Active status.

## Project Management

URL: `/admin-panel/projects/`

Admins can:

- View projects.
- Add projects.
- Edit project code/name/domain/status.
- Delete projects.

Project fields:

- Code.
- Name.
- Domain: `Corporate` or `Non-Corporate`.
- Active status.

## Checklist Management

URL: `/admin-panel/checklists/`

Admins can:

- Search by checklist ID or name.
- Filter by checklist type.
- Filter by active/inactive status.
- Create checklist.
- Edit checklist.
- Preview checklist.
- Download PDF.
- Toggle checklist active status.
- Delete checklist.

## Creating a Checklist

URL: `/admin-panel/checklists/create/`

Steps:

1. Open Checklist page.
2. Click create checklist.
3. Edit checklist metadata:
   - Checklist ID.
   - Checklist name.
   - Checklist type.
   - Projects.
   - Departments.
4. Add sections.
5. Add questions within sections.
6. Select question type.
7. Add options if required by the question type.
8. Mark required questions.
9. Preview if needed.
10. Save checklist.

The backend validates:

- Checklist ID is present and unique.
- Checklist name is present.
- Checklist type is active and valid.
- Selected projects/departments are active and valid.
- At least one section exists.
- Each section contains at least one question.
- Every question has text and valid type.
- Option-based questions have at least one option.

## Editing a Checklist

URL: `/admin-panel/checklists/<id>/edit/`

Editing allows:

- Updating metadata.
- Updating project/department assignments.
- Adding/removing/reordering sections.
- Adding/removing/reordering questions.
- Updating question options and required flags.

When saved, questions missing from the submitted builder state are deleted.

## Checklist Preview and PDF

Preview URL:

- `/admin-panel/checklists/<id>/view/`

PDF URL:

- `/admin-panel/checklists/<id>/pdf/`

PDF export uses WeasyPrint. If WeasyPrint is unavailable, the view returns a service-unavailable text response.

## Response Management

URL: `/admin-panel/responses/`

Admins can:

- Filter responses by project.
- Filter by department.
- Filter by status.
- Filter by submitted date range.
- Search by checklist ID, checklist name, or submitter username.
- View chart summaries.
- View response details.
- Edit eligible responses.
- Approve responses.
- Reject responses.
- Toggle status.
- Delete responses.
- Configure visible columns/actions per role.

## Role-Based Response Control Panel

Located on the Response page.

Admins can configure, per role:

- Visible columns.
- Allowed actions.

Roles:

- User.
- HOD.
- Management.
- Admin row is displayed, but Admin full access is hardcoded by the backend service.

Allowed columns:

- Checklist ID.
- Checklist Name.
- Checklist Type.
- Submitted By.
- Project.
- Department.
- HOD Name.
- Submission DateTime.
- Status.
- Last Updated By.
- Last Updated.
- Actions.

Allowed actions:

- View.
- Edit.
- Approve.
- Reject.
- Delete.
- Toggle.

Backend role ceilings still restrict actions by role.

## Logs

URL: `/admin-panel/logs/`

Admins can review activity logs and filter by:

- Search text.
- Date range.
- Department.
- User.
- Project.
- Action type.
- Status.

Logged activity includes:

- Login success/failure.
- Logout.
- Profile image update.
- Password changes.
- Checklist viewed/printed/PDF downloaded.
- Checklist created/updated/deleted/status toggled.
- Checklist submitted/WIP saved.
- Response approved/rejected/deleted/toggled.
- Permission changes.
- User, department, and project changes.

## Control Panel

URL: `/admin-panel/control-panel/`

Admins can configure:

- Web app name.
- Global theme color.
- Theme mode.
- Button style.
- Font family.
- Layout width.
- Logo.
- Favicon.

Changes require current admin password confirmation.

Uploaded branding image constraints:

- Allowed MIME types include PNG, JPEG, WEBP, SVG, ICO.
- Size limit is 2MB.

## Admin Profile

URL: `/admin-panel/profile/`

Admins can:

- Update profile image using crop UI.
- Change password.

## Operational Recommendations for Admins

- Keep departments and projects active/inactive rather than deleting if historical reporting matters.
- Avoid deleting checklist definitions that already have responses unless data loss is intentional.
- Configure role permissions after creating role workflows.
- Review logs regularly for failed logins and unexpected admin actions.
- Use checklist IDs consistently, such as `CL01`, `CL02`, etc.
