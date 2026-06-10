# QCMS System Improvement Plan

This plan is based on the architecture audit findings and organizes improvements into six implementation phases. It is intended to guide technical remediation, product maturity, and production readiness without changing the current application code.

## Phase 1 - Critical Fixes

### 1. Move Development Secrets and Settings Out of Source

- Description: Replace hardcoded `SECRET_KEY`, `DEBUG=True`, and empty `ALLOWED_HOSTS` with environment-based configuration. Add separate development and production settings strategy.
- Files impacted: `qcms/settings.py`, deployment environment files, optional `.env.example`.
- Estimated complexity: Medium.
- Priority: Critical.
- Dependencies: Deployment environment variable strategy.
- Expected business impact: Prevents exposure of cryptographic signing keys and accidental public deployment in debug mode.

### 2. Fix Stored XSS in Response Detail Modals

- Description: Replace unsafe `innerHTML` rendering of checklist IDs, names, questions, answers, and file URLs with escaped DOM construction or strict escaping helpers.
- Files impacted: `frontend/static/admin_panel/admin_responses.js`, `frontend/static/user_panel/my_submissions.js`.
- Estimated complexity: Medium.
- Priority: Critical.
- Dependencies: None.
- Expected business impact: Protects Admin, HOD, Management, and User sessions from malicious checklist/answer content.

### 3. Restrict Checklist Answer Uploads

- Description: Add file size, extension, MIME type, and content validation for checklist answer uploads. Reject risky types such as HTML/SVG/scriptable files unless securely handled.
- Files impacted: `backend/models.py`, `backend/views/user_panel.py`, possible new upload validation helper/service, tests.
- Estimated complexity: Medium.
- Priority: Critical.
- Dependencies: Business decision on allowed attachment types.
- Expected business impact: Reduces malware hosting, data leakage, and browser execution risk from uploaded content.

### 4. Protect Sensitive Media Access

- Description: Replace direct public access for sensitive checklist upload files with authenticated download views and role-scoped authorization.
- Files impacted: `qcms/urls.py`, `backend/urls.py`, `backend/views/user_panel.py` or new media/download view module, templates/JS that link files.
- Estimated complexity: High.
- Priority: Critical.
- Dependencies: Upload validation policy and storage approach.
- Expected business impact: Prevents unauthorized access to uploaded checklist evidence and response attachments.

### 5. Normalize Response Status Usage

- Description: Decide whether `Pending` or `Pending for Approval` is the canonical submitted status, then update creation, dashboard counts, filters, and transitions consistently.
- Files impacted: `backend/workflow_service.py`, `backend/views/user_panel.py`, `backend/views/admin.py`, `frontend/templates/admin_panel/admin_responses.html`, tests, migrations if data migration is needed.
- Estimated complexity: High.
- Priority: Critical.
- Dependencies: Business approval of final workflow terminology.
- Expected business impact: Prevents reporting errors and review confusion in live operations.

## Phase 2 - Security Hardening

### 1. Enable Production HTTPS Security Settings

- Description: Configure HTTPS redirect, secure session cookies, secure CSRF cookies, HSTS, content type sniffing protection, and frame protection.
- Files impacted: `qcms/settings.py`, production deployment settings.
- Estimated complexity: Low to Medium.
- Priority: High.
- Dependencies: Confirm stable HTTPS deployment.
- Expected business impact: Protects sessions and credentials in production environments.

### 2. Add Login Rate Limiting and Lockout

- Description: Add throttling for failed login attempts by username and IP. Consider lockout, cooldown, and alerting.
- Files impacted: `backend/views/auth.py`, possible new security service/model/cache config, tests.
- Estimated complexity: Medium.
- Priority: High.
- Dependencies: Cache backend or database-backed throttle decision.
- Expected business impact: Reduces brute-force and credential stuffing risk.

### 3. Enforce Active Profile Status

- Description: Ensure users with inactive `UserProfile.is_active=False` cannot operate the system after login. Apply consistent checks at login or middleware level.
- Files impacted: `backend/views/auth.py`, `backend/views/common.py`, possible middleware, tests.
- Estimated complexity: Medium.
- Priority: High.
- Dependencies: Business rule for inactive users and active Django `User.is_active`.
- Expected business impact: Prevents deactivated staff from using QCMS.

### 4. Harden Branding Uploads

- Description: Restrict logo/favicon uploads to safe raster/image types or sanitize SVGs. Validate file content and dimensions.
- Files impacted: `backend/views/admin.py`, `backend/models.py`, control panel template if messaging changes, tests.
- Estimated complexity: Medium.
- Priority: High.
- Dependencies: Branding format policy.
- Expected business impact: Prevents scriptable branding assets and improves platform safety.

### 5. Add Content Security Policy

- Description: Add CSP headers to reduce XSS impact. Decide whether to self-host Chart.js and fonts or allow specific external origins.
- Files impacted: `qcms/settings.py`, templates using CDN resources, possible middleware.
- Estimated complexity: Medium.
- Priority: High.
- Dependencies: External asset strategy.
- Expected business impact: Adds browser-level defense against script injection.

### 6. Add Security-Focused Tests

- Description: Add tests for upload rejection, unauthorized media access, inactive profile access, workflow action denial, and XSS-safe JSON rendering.
- Files impacted: `backend/tests.py` or new test modules.
- Estimated complexity: Medium.
- Priority: High.
- Dependencies: Completion of related security fixes.
- Expected business impact: Prevents regressions in high-risk areas.

## Phase 3 - Performance Optimization

### 1. Add Composite Response Indexes

- Description: Add indexes for common response filters and sort patterns, especially status/date/project/department/submitted_by combinations.
- Files impacted: `backend/models.py`, new migration.
- Estimated complexity: Medium.
- Priority: High.
- Dependencies: Query review and expected production database.
- Expected business impact: Faster response pages, dashboards, and scoped review queues as data grows.

### 2. Add Unique Constraint for Checklist Answers

- Description: Enforce one answer per response/question pair.
- Files impacted: `backend/models.py`, new migration, data cleanup if duplicates exist.
- Estimated complexity: Medium.
- Priority: High.
- Dependencies: Duplicate data audit.
- Expected business impact: Improves data integrity and prevents inconsistent submissions.

### 3. Optimize Admin Dashboard Aggregates

- Description: Reduce repeated count queries and expensive chart queries. Use grouped aggregations, caching, or precomputed reporting tables.
- Files impacted: `backend/views/admin.py`, optional reporting service/cache config.
- Estimated complexity: Medium to High.
- Priority: Medium.
- Dependencies: Database volume and reporting requirements.
- Expected business impact: Faster admin dashboard load time and better scalability.

### 4. Cache Global App Settings

- Description: Cache `AppSettings.get_solo()` used by the global branding context processor to avoid one settings query per rendered page.
- Files impacted: `qcms/context_processors.py`, `backend/models.py`, `backend/views/admin.py` for cache invalidation after control panel saves.
- Estimated complexity: Medium.
- Priority: Medium.
- Dependencies: Cache backend or in-process cache decision.
- Expected business impact: Reduces database load on every page render.

### 5. Improve Query Consistency With Select/Prefetch

- Description: Audit response, checklist, and user listing views for N+1 query risks and ensure consistent use of `select_related` and `prefetch_related`.
- Files impacted: `backend/views/admin.py`, `backend/views/user_panel.py`, `backend/permission_service.py`.
- Estimated complexity: Medium.
- Priority: Medium.
- Dependencies: Query profiling data.
- Expected business impact: Improves page performance under larger datasets.

### 6. Replace Full-Table Log Filters With Indexed Search Strategy

- Description: Improve activity log filtering with appropriate indexes and potentially full-text search depending on database choice.
- Files impacted: `backend/models.py`, `backend/views/admin.py`, migrations.
- Estimated complexity: Medium.
- Priority: Medium.
- Dependencies: Production database selection.
- Expected business impact: Keeps audit log pages usable as logs grow.

## Phase 4 - Workflow Improvements

### 1. Add Review Comments

- Description: Allow HOD, Management, and Admin reviewers to add comments when approving or rejecting responses.
- Files impacted: `backend/models.py`, migrations, `backend/views/admin.py`, `backend/views/user_panel.py`, response templates, JS, tests.
- Estimated complexity: High.
- Priority: High.
- Dependencies: Status normalization.
- Expected business impact: Improves accountability and gives submitters actionable rejection reasons.

### 2. Add Response History Timeline

- Description: Store and display response status changes, reviewer, timestamp, and comments in a timeline.
- Files impacted: New model, migrations, response views/templates, logging service integration.
- Estimated complexity: High.
- Priority: High.
- Dependencies: Review comment model or workflow event model.
- Expected business impact: Gives complete traceability for audits and quality reviews.

### 3. Build Dedicated HOD Review Queue

- Description: Add a route/page focused on responses awaiting HOD review, scoped to the HOD's department/project.
- Files impacted: `backend/urls.py`, `backend/views/user_panel.py` or new HOD view module, templates, sidebar configuration.
- Estimated complexity: Medium.
- Priority: Medium.
- Dependencies: Final approval workflow rules.
- Expected business impact: Reduces reviewer friction and speeds up approvals.

### 4. Improve Workflow Action Feedback

- Description: Replace silent reloads with clear success/error feedback for approve, reject, toggle, edit, and delete actions.
- Files impacted: `frontend/static/admin_panel/admin_responses.js`, `frontend/static/user_panel/my_submissions.js`, response templates.
- Estimated complexity: Medium.
- Priority: Medium.
- Dependencies: None.
- Expected business impact: Fewer user support issues and clearer operational confidence.

### 5. Add Notification Hooks

- Description: Add internal notification records or email hooks for submission, approval, rejection, and resubmission.
- Files impacted: New notification model/service, workflow/action views, templates.
- Estimated complexity: High.
- Priority: Medium.
- Dependencies: Email/in-app notification strategy.
- Expected business impact: Improves turnaround time and user awareness.

### 6. Add Checklist Versioning

- Description: Preserve historical versions of checklist definitions so responses remain tied to the exact questions used at submission time.
- Files impacted: `backend/models.py`, checklist builder views, response fill logic, migrations, tests.
- Estimated complexity: High.
- Priority: Medium.
- Dependencies: Data model design.
- Expected business impact: Stronger auditability and safer checklist edits over time.

## Phase 5 - Enterprise Features

### 1. Export Responses to Excel/CSV

- Description: Add export functionality for filtered response lists, including answers and metadata.
- Files impacted: `backend/views/admin.py` or reporting module, `backend/urls.py`, admin response template.
- Estimated complexity: Medium.
- Priority: Medium.
- Dependencies: Export format and permission rules.
- Expected business impact: Supports audits, offline reporting, and management review.

### 2. Advanced Reporting Dashboard

- Description: Add project, department, checklist type, status, aging, and trend reports.
- Files impacted: New reporting views/services/templates/static JS, possibly new indexes/materialized data.
- Estimated complexity: High.
- Priority: Medium.
- Dependencies: Performance optimization and reporting requirements.
- Expected business impact: Enables data-driven quality governance.

### 3. Import Master Data and Checklist Templates

- Description: Support CSV/XLSX import for users, departments, projects, checklist types, and checklist definitions.
- Files impacted: New import views/services/templates, validation logic, tests.
- Estimated complexity: High.
- Priority: Medium.
- Dependencies: File format specification.
- Expected business impact: Reduces admin setup effort and improves onboarding speed.

### 4. Fine-Grained Permission Model

- Description: Move beyond role-level actions into permission policies by module, project, department, and workflow state.
- Files impacted: `backend/permission_service.py`, `backend/models.py`, admin permission UI, tests.
- Estimated complexity: High.
- Priority: Medium.
- Dependencies: Business authorization model.
- Expected business impact: Supports larger organizations with stricter control requirements.

### 5. Enterprise Identity Integration

- Description: Add SSO support through SAML/OIDC or organization identity provider.
- Files impacted: Authentication settings, login flow, user provisioning/sync logic.
- Estimated complexity: High.
- Priority: Low to Medium.
- Dependencies: Identity provider details.
- Expected business impact: Improves security, reduces password management burden, supports enterprise adoption.

### 6. Audit Log Export and Retention Policy

- Description: Add export, retention, archival, and purge rules for `ActivityLog`.
- Files impacted: `backend/models.py`, `backend/views/admin.py`, admin logs template, management command or scheduled task.
- Estimated complexity: Medium.
- Priority: Medium.
- Dependencies: Compliance and retention requirements.
- Expected business impact: Supports compliance audits and controls long-term database growth.

## Phase 6 - Scalability Enhancements

### 1. Migrate Production Database to PostgreSQL

- Description: Replace SQLite for production with PostgreSQL and tune database settings.
- Files impacted: `qcms/settings.py`, deployment configuration, migration/backup scripts.
- Estimated complexity: Medium to High.
- Priority: High.
- Dependencies: Production infrastructure.
- Expected business impact: Enables reliable concurrent usage and larger datasets.

### 2. Introduce Background Jobs

- Description: Move heavy operations such as PDF generation, exports, notifications, and scheduled cleanup into background workers.
- Files impacted: New task queue configuration, reporting/export/PDF/notification code.
- Estimated complexity: High.
- Priority: Medium.
- Dependencies: Queue backend selection such as Redis/Celery/RQ.
- Expected business impact: Keeps web requests fast and reliable.

### 3. Use Object Storage for Media

- Description: Move uploaded files and branding assets from local disk to object storage with controlled access.
- Files impacted: Django storage settings, media URLs/download views, deployment configuration.
- Estimated complexity: High.
- Priority: Medium.
- Dependencies: Storage provider and private media strategy.
- Expected business impact: Improves durability, backup, and horizontal scaling.

### 4. Add Application Monitoring and Error Tracking

- Description: Add structured logging, exception tracking, uptime monitoring, and performance metrics.
- Files impacted: `qcms/settings.py`, deployment configuration, logging setup.
- Estimated complexity: Medium.
- Priority: Medium.
- Dependencies: Monitoring platform selection.
- Expected business impact: Faster incident response and better production visibility.

### 5. Add API Layer for Future Integrations

- Description: Introduce a versioned API for checklists, responses, users, and reports if external systems or mobile apps are planned.
- Files impacted: New API app/modules, serializers, permissions, tests.
- Estimated complexity: High.
- Priority: Low to Medium.
- Dependencies: Integration roadmap.
- Expected business impact: Enables integration with mobile apps, BI tools, and enterprise systems.

### 6. Refactor Admin Views Into Domain Modules

- Description: Split the large admin view module into smaller modules for dashboard, users, master data, checklists, responses, settings, and logs.
- Files impacted: `backend/views/admin.py`, `backend/views/__init__.py`, possible new view modules, imports, tests.
- Estimated complexity: Medium.
- Priority: Medium.
- Dependencies: Regression test coverage.
- Expected business impact: Reduces maintenance risk and makes future changes faster and safer.

## Cross-Phase Implementation Notes

- Add tests before or alongside behavior changes.
- Avoid mixing workflow redesign with security fixes in the same release.
- Treat file upload and media access as a production blocker.
- Run `python manage.py check --deploy` before every production release.
- Keep user-facing workflow terminology consistent across backend, templates, reports, and documentation.
- Review migration plans carefully before changing statuses or database constraints.
