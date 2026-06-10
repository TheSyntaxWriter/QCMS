# Future Roadmap

## Security Enhancements

- Split settings into development, staging, and production modules.
- Load secrets from environment variables.
- Disable `DEBUG` in production.
- Configure secure cookies, HTTPS redirect, HSTS, and allowed hosts.
- Add login throttling and account lockout.
- Add upload validation for file type, extension, size, and content.
- Serve checklist answer attachments through authenticated download views.
- Remove SVG from branding uploads or sanitize uploaded SVGs.
- Fix response modal XSS by using DOM APIs or escaping.
- Add Content Security Policy.
- Add Subresource Integrity or self-host external JavaScript libraries.

## Workflow Enhancements

- Consolidate `Pending` and `Pending for Approval` into one canonical submitted status.
- Add review comments for approval/rejection.
- Add response history timeline.
- Add assigned reviewer queues.
- Add escalation rules for overdue approvals.
- Add resubmission flow for rejected responses.
- Add notification events for submit, approve, reject, and reopen.
- Add bulk approve/reject where appropriate.

## Permission Enhancements

- Enforce `UserProfile.is_active` consistently.
- Decide whether `RolePermission.selected_projects` should be active and enforce it.
- Move role logic toward policy classes or Django permissions/groups.
- Add tests for every role/action/status combination.
- Add UI feedback when workflow blocks an action.
- Render action buttons from effective per-response permissions.

## Database Enhancements

- Move production database from SQLite to PostgreSQL.
- Add composite indexes for response filtering/reporting.
- Add uniqueness constraint on `ChecklistAnswer(response, question)`.
- Replace pipe-delimited checkbox answer storage with JSON.
- Consider first-class `ChecklistSection` model if section metadata grows.
- Archive or remove legacy `Checklist`, `Section`, and `Question` models.
- Add soft delete for master data and checklists if historical reporting matters.

## Performance Enhancements

- Cache global `AppSettings`.
- Cache dashboard aggregates or compute them asynchronously.
- Avoid repeated count queries on dashboard pages.
- Add pagination everywhere large tables can grow.
- Add database indexes for search/filter columns.
- Use select/prefetch patterns consistently.
- Move reporting charts to optimized reporting queries.

## UI/UX Enhancements

- Replace browser `alert()` and `confirm()` with styled modals/toasts.
- Add consistent success/error feedback for AJAX actions.
- Add loading indicators during save/export/action calls.
- Improve empty states for dashboards, checklists, and responses.
- Add breadcrumbs for admin pages.
- Add clearer status badges and workflow labels.
- Fix text encoding/mojibake artifacts.
- Add responsive testing for tables and modals.
- Add accessible labels and keyboard support for modals.

## Admin Experience Enhancements

- Add import/export for users, departments, projects, and checklist definitions.
- Add checklist duplication/versioning.
- Add checklist publish/draft states.
- Add response export to Excel/CSV/PDF.
- Add advanced audit log export and retention settings.
- Add admin notifications for failed login spikes or unusual activity.

## Developer Experience Enhancements

- Split large view modules.
- Add service layer tests.
- Add factories/fixtures for common test data.
- Add linting and formatting.
- Add CI pipeline with tests and deployment checks.
- Remove generated artifacts from git tracking.
- Add `.env.example`.
- Add production settings template.
- Add architecture diagrams to docs.

## Scalability Roadmap

### Phase 1: Hardening

- Fix production settings.
- Fix upload handling.
- Fix XSS points.
- Add core workflow tests.
- Add database constraints.

### Phase 2: Workflow Maturity

- Normalize statuses.
- Add review comments/history.
- Add notification system.
- Add HOD queues.

### Phase 3: Reporting

- Add response exports.
- Add chart/reporting service.
- Add historical trend dashboards.
- Add project/department performance views.

### Phase 4: Enterprise Readiness

- Move to PostgreSQL.
- Add background workers for PDF/report generation.
- Add object storage for files.
- Add centralized monitoring.
- Add SSO or enterprise identity integration.
- Add fine-grained permissions.

## Suggested Priority Order

1. Production security settings.
2. Upload validation and private media access.
3. XSS-safe response detail rendering.
4. Status workflow consolidation.
5. Database constraints and indexes.
6. Split admin view module.
7. Add comprehensive permission/workflow tests.
8. Improve dashboard/reporting performance.
9. Improve UI feedback and accessibility.
10. Add notifications and review history.
