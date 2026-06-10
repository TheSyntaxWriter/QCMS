# Documentation Changelog

## 2026-06-10 - Documentation Reorganization

### Changed

- Moved `MASTER_SYSTEM_DOCUMENT.md` into `docs/MASTER_SYSTEM_DOCUMENT.md`.
- Moved `SYSTEM_IMPROVEMENT_PLAN.md` into `docs/SYSTEM_IMPROVEMENT_PLAN.md`.
- Archived older audit/review documents under `docs/archive/audits/`.

### Archived

The following files were archived because their useful long-term content is now covered by the master system document, numbered documentation set, and system improvement plan:

- `PROJECT_AUDIT.md` -> `docs/archive/audits/PROJECT_AUDIT.md`
- `REVIEW_NOTES.md` -> `docs/archive/audits/REVIEW_NOTES.md`
- `ARCH_ANALYSIS_2026-05-26.md` -> `docs/archive/audits/ARCH_ANALYSIS_2026-05-26.md`
- `ARCHITECTURE_RBAC_AUDIT_2026-05-19.md` -> `docs/archive/audits/ARCHITECTURE_RBAC_AUDIT_2026-05-19.md`

### Duplicate Documentation Review

- `docs/MASTER_SYSTEM_DOCUMENT.md` intentionally overlaps the numbered docs and should be treated as the single high-level source of truth.
- `docs/01_Project_Overview.md` through `docs/10_Future_Roadmap.md` remain useful as focused deep-dive documents by topic.
- `docs/SYSTEM_IMPROVEMENT_PLAN.md` overlaps with future-roadmap content but provides execution-ready phased remediation details, so it remains separate.
- The archived audit files contain earlier point-in-time findings and review notes. They should not be used as current implementation guidance unless a historical comparison is needed.

### Current Long-Term Documentation Set

- `docs/MASTER_SYSTEM_DOCUMENT.md`: single source of truth.
- `docs/01_Project_Overview.md`: focused project overview.
- `docs/02_System_Architecture.md`: focused architecture detail.
- `docs/03_Database_Design.md`: model and relationship detail.
- `docs/04_User_Roles_and_Permissions.md`: role and permission detail.
- `docs/05_Checklist_Workflow.md`: checklist, response, and status workflow detail.
- `docs/06_URL_and_Navigation_Flow.md`: URL map and navigation detail.
- `docs/07_Admin_Guide.md`: admin operations.
- `docs/08_Deployment_Guide.md`: deployment and production readiness.
- `docs/09_Developer_Onboarding_Guide.md`: developer setup and extension guide.
- `docs/10_Future_Roadmap.md`: strategic future roadmap.
- `docs/SYSTEM_IMPROVEMENT_PLAN.md`: phased remediation and enhancement plan.
- `docs/CHANGELOG.md`: documentation change history.
