# Future Roadmap

## Current Baseline

The June 2026 stabilization release completed production security settings, XSS-safe response rendering, validated uploads, authenticated media access, assigned-HOD approval, approval comments and rejection reasons, append-only decision and activity history, submit-only geolocation, database-backed in-app notifications, standardized header/cursor/button behavior, and the Universal Table Framework with filtered XLSX export.

## Near-Term Hardening

- Move production deployments from SQLite to PostgreSQL.
- Enforce `UserProfile.is_active` centrally during authentication and request authorization.
- Add login throttling, account lockout, and security monitoring.
- Add Content Security Policy and formal trusted-proxy configuration.
- Add backup/restore verification, error tracking, health checks, and operational runbooks.
- Review and add composite indexes using production query telemetry.
- Add controlled retention and archival policies for notifications and audit logs.

## Architecture and Maintainability

- Split the large Admin and user view modules by business domain.
- Centralize repeated role/profile guards in tested authorization decorators or policies.
- Retire legacy checklist models after data-usage verification.
- Replace pipe-delimited checkbox answers with structured storage after a compatibility migration.
- Cache singleton application settings and optimize repeated dashboard aggregates.
- Add CI linting, formatting, accessibility checks, and visual regression coverage.

## Workflow and Reporting

- Normalize legacy `Pending` records into the canonical submitted status through a controlled migration.
- Add an assigned-HOD work queue with aging and workload indicators.
- Add response and audit reporting dashboards using optimized reporting queries.
- Consider checklist versioning, duplication, publish/draft lifecycle, and soft deletion.
- Add loading states and richer empty states for long-running report and export actions.

## UI and Accessibility

- Replace remaining mojibake/legacy glyph controls with one locally packaged, allowlisted icon registry.
- Complete keyboard-only, screen-reader, high-contrast, reduced-motion, 200% zoom, mobile, and tablet acceptance testing.
- Consolidate remaining page-local CSS after component migration.
- Add optional globally managed card/button visual profiles only after design approval.

## Intentionally Deferred Enterprise Features

The following are outside the stabilization release and require separate business approval and architecture:

- Email, SMS, WhatsApp, and other delivery channels.
- SLA and escalation engines.
- WebSockets or Server-Sent Events.
- External integrations and SSO.
- Object storage and background worker infrastructure.
- Fine-grained enterprise permissions and segregation-of-duties controls.

## Recommended Order

1. PostgreSQL, backups, monitoring, and inactive-profile enforcement.
2. Login throttling, CSP, proxy/IP policy, and retention controls.
3. Legacy status normalization and production index tuning.
4. View-module and authorization-policy refactoring.
5. Reporting performance and checklist versioning.
6. Accessibility automation and icon-system consolidation.
7. Separately approved enterprise integrations and asynchronous infrastructure.
