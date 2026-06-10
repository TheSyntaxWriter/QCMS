# WMS System Architecture & RBAC Audit (2026-05-19)

## 1) Current System Architecture

### 1.1 Stack and high-level layout
- Backend: Django monolith (`backend` app + `qcms` project).
- Database: SQLite (`db.sqlite3`) configured directly in settings.
- Frontend: Django templates + static JS/CSS (server-rendered pages with progressive JS features).
- AuthN/AuthZ: Django session authentication + custom role checks through `UserProfile.role`.

### 1.2 Core domain model
- Master data:
  - `Project` (code, name, domain, is_active).
  - `Department` (code, name, is_active).
- Identity and role profile:
  - `UserProfile` (links Django `User` to role + department + project + is_active).
- Checklist engine (new model set):
  - `ChecklistType`, `ChecklistDefinition`, `ChecklistQuestion`.
  - `ChecklistResponse`, `ChecklistAnswer`.
- Legacy checklist model set still present:
  - `Checklist`, `Section`, `Question` (appears retained for backward compatibility; not used by current builder flow).
- Role-specific dynamic table config:
  - `RolePermission` stores `visible_columns`, `selected_projects`, `allowed_actions`.

### 1.3 URL and view structure
- `backend/urls.py` exposes login/logout/home, user panel routes, management routes, and admin panel routes.
- Role redirection happens centrally in `redirect_for_profile`:
  - User/HOD -> `my_checklists`
  - Management -> `dashboard`
  - Admin -> `admin_dashboard`

### 1.4 Current execution flow
1. User authenticates (`/login/`).
2. Home redirect routes user to role landing page.
3. Each view manually checks:
   - authenticated
   - expected role
4. Data scope for non-admin pages is mostly handled in query helper functions:
   - checklist visibility by role/department/project/domain
   - response visibility by role

---

## 2) Current Role Capabilities (what is actually implemented)

## 2.1 Normal User
### Available now
- Can log in/out.
- Can access:
  - `my_checklists`
  - `my_submissions`
  - `profile`
- Checklist list is filtered by:
  - same department AND (same project OR same project-domain).
- Submission list is filtered to `submitted_by == current user`.
- UI actions/columns in submissions are controlled by `RolePermission` if set; otherwise defaults are permissive.

### Not available / missing
- No implemented checklist fill/submit endpoint in current URL map.
- No explicit draft, resubmit, or withdrawal workflow.
- No direct dashboard route.

## 2.2 HOD (Head of Department)
### Available now
- Uses same landing and pages as normal user (`my_checklists`, `my_submissions`, `profile`).
- Sees checklists for their department.
- Sees submissions for their department.

### Partially implemented / missing
- No dedicated HOD dashboard route/view in current URL map.
- No HOD-specific approval endpoint separated from admin actions.
- No enforced “HOD-only approve” state transition logic.

## 2.3 Management
### Available now
- Redirect target is `dashboard` (user panel dashboard template).
- Can access `my_checklists`, `my_submissions`, `profile`, and `dashboard`.
- Data access is broad:
  - all checklist definitions in `_checklists_for_profile`.
  - all responses in `_responses_for_profile`.

### Partially implemented / missing
- Separate `management_dashboard` view exists, but renders `management_dashboard.html`, which is not present in the templates listed and is not the main role landing route.
- No clear management approval boundaries distinct from admin.

## 2.4 Management/Admin (Admin role)
### Available now
- Full admin panel pages:
  - dashboard
  - users CRUD-ish actions
  - departments CRUD-ish actions
  - projects CRUD-ish actions
  - checklist create/edit/view/pdf
  - response listing + action controls
  - role permission popup for User/HOD/Management/Admin rows
- Can update response status (approve/reject/toggle) and delete responses.
- Can set `RolePermission` via `save_permissions` endpoint.

### Gaps/risk areas
- Several admin actions perform hard deletes without dependency safety checks.
- Some action handlers multiplex multiple POST intents in one endpoint, increasing complexity and audit risk.

---

## 3) Working vs Partial/Missing Modules

## 3.1 Fully working (as implemented)
- Authentication (session login/logout).
- Role-based landing redirects.
- Admin master maintenance pages and create/edit/delete/toggle flows (Users/Departments/Projects).
- Checklist builder (create/edit with validation for sections/questions/options).
- Checklist preview + PDF generation (with WeasyPrint dependency).
- Admin responses filters, charts, pagination, modal detail view.
- RolePermission persistence and consumption in My Submissions table rendering.

## 3.2 Partially implemented
- RolePermission is only strongly used for table UI visibility/actions; not consistently enforced as backend authorization policy.
- `selected_projects` in `RolePermission` is stored but not effectively enforced in response queries for user/HOD/management pages.
- `management_dashboard` route/view layer is inconsistent with main management route and template availability.

## 3.3 Missing or functionally absent
- End-user checklist submission creation flow (no obvious create response endpoint in route map).
- Dedicated HOD approval workflow and SLA/escalation states.
- Multi-stage approvals (User -> HOD -> Management) with explicit state machine.
- Enterprise audit trail (immutable action logs with before/after data and actor metadata).
- Notification framework (email/in-app triggers for submit/approve/reject/escalate).

---

## 4) Current Workflow & Role Flow

## Implemented workflow (practical)
1. Admin configures masters (users/departments/projects/checklists).
2. User/HOD/Management can browse checklists depending on filters.
3. Existing responses can be viewed in role-scoped pages.
4. Admin can approve/reject/toggle/delete responses from admin panel.

## Intended-but-not-fully-enforced role flow
- System suggests role-specific views and permissions, but backend transition control is not strict enough to guarantee clean enterprise approval chains.

---

## 5) Current Security & Permission Gaps

1. **Authorization by role string checks only**
   - Repeated manual checks (`profile.role == ...`) instead of centralized permission classes/decorators.
2. **UI permissions vs backend permissions mismatch risk**
   - Table hides actions by `allowed_actions`, but backend endpoints do not consistently re-check fine-grained action policy beyond Admin role.
3. **Overly broad default permissions fallback**
   - If `RolePermission` missing, defaults include approve/reject/delete/toggle for user-panel rendering.
4. **No immutable audit log**
   - `updated_by` and status update timestamps exist, but no append-only action journal.
5. **No object-level row security framework**
   - Department/project scoping handled ad hoc in helper functions; not enforced globally.
6. **Hard-delete usage**
   - Users/departments/projects/checklists/responses can be physically deleted, risking referential/business-history loss.
7. **Potential template/route drift**
   - Legacy/alternate routes and partially-used management view increase maintenance risk.

---

## 6) UX Improvement Areas

- Add role-focused dashboards:
  - User: pending forms, due dates, recent submissions.
  - HOD: review queue, SLA aging, department KPIs.
  - Management: org-level trends and bottlenecks.
- Replace “toggle” wording with explicit state actions (activate/deactivate, reopen/reject).
- Provide clear empty states (“No checklists assigned for your department/project”).
- Add form autosave/draft for checklist responses.
- Improve error messages for validation failures in builder and master forms.
- Standardize action confirmations and success toasts across all modules.

---

## 7) Recommended Enterprise RBAC Structure

## 7.1 Role hierarchy (recommended)
- **System Admin**
  - Platform config, role management, master data governance, audit access.
- **Management Approver**
  - Final approval authority across scoped org units.
- **HOD Approver**
  - Department-level review/approve/reject for assigned departments.
- **Standard User (Submitter)**
  - Create/edit own drafts, submit, view own history.
- **Auditor (Read-only)** (optional new role)
  - Cross-cutting read-only visibility with export rights.

## 7.2 Permission model (recommended)
Use policy tuples: `resource.action.scope`.
- Resource examples: `checklist_definition`, `checklist_response`, `user_profile`, `project`, `department`, `audit_log`.
- Actions: `create`, `read`, `update`, `delete`, `approve`, `reject`, `assign`, `export`.
- Scope: `own`, `department`, `project`, `org`, `all`.

Example:
- User: `checklist_response.create.own`, `checklist_response.update.own_draft`, `checklist_response.read.own`.
- HOD: `checklist_response.read.department`, `checklist_response.approve.department`.
- Management: `checklist_response.read.org`, `checklist_response.approve.org_final`.
- Admin: `role_permission.manage.all`, `master_data.manage.all`.

## 7.3 Dashboard access
- Enforce separate dashboards and APIs by role.
- Dashboard widgets should be policy-bound (widget hidden if permission missing).
- Never rely on frontend hiding alone.

## 7.4 Approval workflows
Adopt explicit finite states:
- `Draft -> Submitted -> HOD_Approved/HOD_Rejected -> Mgmt_Approved/Mgmt_Rejected -> Closed`.
- Add SLA timers, escalation, and reopen policy.
- Track each transition in `ApprovalActionLog` with actor, from_state, to_state, reason.

## 7.5 Data visibility restrictions
- Own-only (User).
- Department-scoped (HOD).
- Org/project scoped (Management).
- All with governance (Admin).
- Enforce via centralized queryset policy service or Django custom manager.

## 7.6 Audit logs & tracking
Implement append-only logs for:
- auth events (login success/failure, logout)
- CRUD and state transitions
- permission changes (`RolePermission` edits)
- file access/download actions

Minimum fields:
- actor_user_id, actor_role, action, resource_type, resource_id, old_value, new_value, ip, user_agent, timestamp.

## 7.7 Notifications
- Trigger on: submission, assignment, approval, rejection, escalation, due reminder.
- Role-based channels:
  - in-app mandatory
  - email optional by policy
- Per-user notification preferences with admin override for compliance-critical alerts.

## 7.8 Form/edit/delete restrictions
- User can edit only Draft and own responses.
- HOD cannot edit content, only approve/reject with reason.
- Management final approval only; no content edits after HOD approval.
- Prefer soft-delete (`is_active` / `is_deleted`) + archive, not hard delete.

## 7.9 Best practices for scalable enterprise role management
- Central policy engine (single source of truth for permissions).
- Permission seeding/migrations per release.
- Deny-by-default fallback.
- Full backend enforcement + frontend mirroring.
- Periodic access review reports.
- Segregation-of-duties controls (creator cannot final-approve same record).
- Extensive tests: role matrix + object-level access + workflow transitions.

---

## 8) Comparison Table: Current vs Recommended Capabilities

| Area | Current Capability | Recommended Capability |
|---|---|---|
| Role model | 4 role strings in `UserProfile` | Hierarchical RBAC with policy tuples and optional Auditor role |
| Permission storage | `RolePermission` JSON for columns/actions | Normalized permissions + scopes + backend policy checks |
| Enforcement | Mostly view-level role checks | Centralized decorator/service + object-level enforcement |
| User submissions | Listing exists; create flow unclear/missing | Full draft/submit/edit-own workflow |
| HOD workflow | Department visibility only; no dedicated approval pipeline | Explicit HOD queue + approve/reject reasons + SLA |
| Management workflow | Broad visibility; mixed dashboard paths | Final approval stage + org analytics dashboard |
| Admin controls | Broad CRUD/actions | Governed admin with soft-delete, dependency checks, SoD rules |
| Audit trail | Limited (`updated_by`, timestamps) | Immutable event logs with before/after payloads |
| Notifications | Not implemented | Event-driven in-app/email notifications with preferences |
| Data restrictions | Ad hoc query filters | Standardized scope-based row-level policy |
| Delete behavior | Hard deletes used in several modules | Soft-delete/archive + retention policy |
| UX consistency | Mixed terminology and role UI overlap | Role-centric dashboards and workflow-specific actions |

---

## 9) Concrete Change Plan (priority order)

### Phase 1 (Security baseline)
1. Add centralized `@role_required` + policy helper for object-scope filtering.
2. Deny-by-default permissions when `RolePermission` missing.
3. Replace hard deletes with soft delete for business entities/responses.
4. Add audit log model + middleware/hooks for critical actions.

### Phase 2 (Workflow correctness)
5. Implement checklist response create/edit/submit flow.
6. Introduce explicit approval states and transition guards.
7. Build separate HOD and Management review queues.

### Phase 3 (Usability and scale)
8. Role-specific dashboards + actionable KPI cards.
9. Notification service (submit/approve/reject/escalation).
10. Expand test suite with role-permission matrix and transition tests.

