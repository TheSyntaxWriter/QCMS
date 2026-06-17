# QCMS Final Pending Items Report

## 1. Confirmed Issues Found

This report uses the completed repository review and the findings already collected before interruption. No new responsive audit, temporary database creation, or browser automation was performed for this final report.

### 1.1 Header Identity Inconsistencies

Requirement: every authenticated page and every role must show:

```text
Welcome, <Full Name>
```

Confirmed current behavior:

| Area | Current Issue | Evidence |
|---|---|---|
| Admin base default | Shows `Welcome, Admin` when a child template does not override `topbar_welcome`. | `frontend/templates/admin_panel/admin_base.html` |
| User/HOD/Management base default | Shows `Welcome` when a child template does not override `topbar_welcome`. | `frontend/templates/user_panel/base_user.html` |
| Control Panel | Shows `Enterprise Configuration` instead of the authenticated user's full name. | `frontend/templates/admin_panel/admin_control_panel.html` |
| Notification Control | Shows `Control Panel` instead of the authenticated user's full name. | `frontend/templates/admin_panel/admin_notification_settings.html` |
| Admin checklist preview | Shows checklist ID in the right header identity area. | `frontend/templates/admin_panel/checklist_view.html` |
| User checklist preview | Shows checklist ID in the right header identity area. | `frontend/templates/user_panel/checklist_view.html` |
| Admin pages without explicit override | Inherit `Welcome, Admin` rather than full name. | Admin templates using `admin_base.html` without overriding `topbar_welcome` |

Root cause:

- The header identity text is still controlled by per-template `{% block topbar_welcome %}` overrides.
- Some pages use the right-side identity area for module context instead of user identity.
- The shared avatar is centralized, but the welcome text is not yet centralized.

Required correction:

- Remove page-specific identity text from `topbar_welcome`.
- Make both authenticated base templates render `Welcome, {{ request.user.get_full_name|default:request.user.username }}` directly.
- Move module-specific labels such as checklist ID, `Enterprise Configuration`, and `Control Panel` into the left page title area or page content header.

### 1.2 Missing Global Icon Gallery

Confirmed status: not implemented.

Current implementation:

- Sidebar icons use fixed CSS mask classes such as `.app-icon--dashboard`, `.app-icon--checklist`, `.app-icon--response`, and related classes.
- Notification bell still uses a glyph in `frontend/templates/shared/notification_center.html`.
- Several page headings and controls still use emoji/text glyphs, for example the Users heading.
- No Lucide icon registry exists.
- No `ICON_REGISTRY`, semantic icon slot mapping, icon picker, icon preview, or Admin-managed icon assignment system exists.
- No stored `icon_slots` or `icon_assignments` configuration is consumed by the UI.

Remaining work:

- Package one local icon library, preferably Lucide.
- Create a safe allowlisted icon registry.
- Define semantic icon slots for navigation, dashboard, actions, logs, notifications, profile, logout, checklist, user, department, project, settings, approve, reject, export, search, and close.
- Store only allowlisted icon keys in `AppSettings.theme_settings`.
- Build an Admin Icon Gallery section under Control Panel.
- Add searchable picker, category filter, live preview, reset per slot, and reset all.
- Replace CSS masks, emoji controls, and text glyphs with the shared icon renderer.

### 1.3 Mobile Responsiveness Gaps

The responsive audit was interrupted before full browser measurement could complete. The following gaps are confirmed from code review and prior collected findings:

| Area | Confirmed Gap |
|---|---|
| Tables | Business tables rely on horizontal `.table-responsive` overflow. This prevents clipping, but still produces horizontal table scrolling on narrow widths. |
| Notification Control | The event matrix is wide and is contained by horizontal scrolling rather than adapting into a compact mobile settings layout. |
| Admin base header | Topbar uses a two-column flex row; long module titles and the identity group can become cramped on narrow widths. |
| User/HOD/Management base header | Same topbar structure as Admin, with limited responsive header behavior beyond hiding long welcome text in CSS. |
| Checklist builder/create pages | Large builder sections and metadata matrices still have specialized layouts and are not fully migrated to a universal responsive component system. |
| Response permission matrix | Role permission controls are a configuration matrix with custom responsive behavior; not yet unified under a settings-table variant. |
| Profile crop modal | Recently optimized and verified separately for desktop, mobile portrait, short mobile, and landscape. No pending issue from that flow. |
| Sidebar | Shared sidebar is responsive, but final verification across all audited widths was interrupted and remains a manual QA task before release. |

Important limitation:

- Width-specific pass/fail results for `320`, `375`, `390`, `412`, `768`, and `1024` were not completed in the interrupted responsive run.
- Do not treat this report as a completed visual regression matrix. Treat it as an implementation-ready pending-items report based on already collected evidence.

### 1.4 Additional Confirmed UI/UX Issues

| Issue | Severity | Evidence |
|---|---:|---|
| Welcome identity text is duplicated through template blocks instead of one shared rule. | High | `admin_base.html`, `base_user.html`, child template overrides |
| Icon system remains fragmented. | High | `sidebar.css`, `notification_center.html`, page headings |
| Global Icon Gallery is absent. | High | No registry/model/template/control implementation found |
| Notification Control still lacks enterprise master-plan enhancements such as categories, history page, test notification, templates, role/user preferences, configurable popup duration, acknowledgement, and delivery history. | Medium | `NOTIFICATION_CENTER_MASTER_PLAN.md` vs current implementation |
| Control Panel 2.0 Phase 1 intentionally excludes Icon Gallery and dark mode. | Medium | Control Panel implementation and exclusions |
| Page-specific CSS still competes with shared UI rules in several modules. | Medium | Base templates and module styles still define `.btn`, table, card, and surface rules |
| Notification bell uses a text/glyph symbol instead of the future icon renderer. | Low | `frontend/templates/shared/notification_center.html` |
| Some headings still use emoji, for example Users Management. | Low | `frontend/templates/admin_panel/admin_users.html` |

## 2. Exact Files That Must Be Modified

### 2.1 Header Identity Fix

Required files:

- `frontend/templates/admin_panel/admin_base.html`
- `frontend/templates/user_panel/base_user.html`
- `frontend/templates/admin_panel/admin_control_panel.html`
- `frontend/templates/admin_panel/admin_notification_settings.html`
- `frontend/templates/admin_panel/checklist_view.html`
- `frontend/templates/user_panel/checklist_view.html`
- Any Admin child template that currently relies on the default `Welcome, Admin`
- Any User/HOD/Management child template that currently relies on the default `Welcome`

Recommended supporting tests:

- `backend/tests.py`

Implementation target:

- Centralize the right-side header text in the base templates.
- Keep `topbar_title` for page/module context only.
- Remove or ignore `topbar_welcome` overrides after migration.

### 2.2 Global Icon Gallery

Required backend files:

- `backend/control_panel_settings.py`
- `backend/views/admin.py`
- `qcms/context_processors.py`
- `backend/tests.py`

Required template files:

- `frontend/templates/admin_panel/admin_control_panel.html`
- `frontend/templates/admin_panel/partials/control_panel_nav.html`
- `frontend/templates/admin_panel/partials/sidebar.html`
- `frontend/templates/shared/notification_center.html`
- New shared icon renderer partial, recommended:
  - `frontend/templates/shared/icon.html`

Required static files:

- `frontend/static/shared/sidebar.css`
- `frontend/static/shared/ui_system.css`
- `frontend/static/shared/control_panel.css`
- New local icon asset/registry file, recommended:
  - `frontend/static/shared/icons.css`
  - or `frontend/static/shared/icon_registry.js` if a static preview helper is needed

Optional supporting backend module:

- `backend/icon_registry.py`

Implementation target:

- Store only allowlisted icon keys.
- Never store raw SVG, HTML, JavaScript, or remote icon URLs in Admin settings.

### 2.3 Mobile and Responsive Cleanup

Likely files:

- `frontend/static/shared/ui_system.css`
- `frontend/static/shared/table_system.css`
- `frontend/static/shared/sidebar.css`
- `frontend/static/shared/control_panel.css`
- `frontend/static/shared/profile.css`
- `frontend/templates/admin_panel/admin_base.html`
- `frontend/templates/user_panel/base_user.html`
- `frontend/templates/admin_panel/admin_users.html`
- `frontend/templates/admin_panel/admin_departments.html`
- `frontend/templates/admin_panel/admin_projects.html`
- `frontend/templates/admin_panel/admin_checklists.html`
- `frontend/templates/admin_panel/admin_responses.html`
- `frontend/templates/admin_panel/admin_logs.html`
- `frontend/templates/admin_panel/admin_notification_settings.html`
- `frontend/templates/user_panel/my_checklists.html`
- `frontend/templates/user_panel/my_submissions.html`
- `frontend/templates/user_panel/checklist_fill.html`
- `frontend/templates/admin_panel/checklist_create.html`
- `frontend/templates/admin_panel/partials/response_table.html`
- `frontend/templates/admin_panel/partials/checklist_table.html`
- `frontend/templates/shared/tables/pagination.html`

Implementation target:

- Preserve table horizontal scrolling where unavoidable, but improve toolbar stacking and control access.
- Convert configuration matrices to shared settings-table variants.
- Ensure no controls disappear at narrow widths.
- Perform the interrupted width checks separately before final release.

### 2.4 Notification Center Enterprise Enhancements

Likely files:

- `backend/models.py`
- `backend/notification_service.py`
- `backend/views/notifications.py`
- `backend/views/admin.py`
- `backend/tests.py`
- `frontend/templates/admin_panel/admin_notification_settings.html`
- `frontend/templates/shared/notification_center.html`
- `frontend/static/shared/notification_center.js`
- `frontend/static/shared/notification_center.css`
- `frontend/static/shared/control_panel.css`

Potential migrations:

- Add only when implementing categories, templates, history/search, role/user preferences, acknowledgement, or delivery attempts.

## 3. Recommended Implementation Order

### Step 1: Header Identity Consistency

Priority: High

Why first:

- Smallest surface area.
- Directly violates the explicit final requirement.
- Low database risk.
- Improves every authenticated page immediately.

Acceptance:

- Every authenticated page shows `Welcome, <Full Name>` in the identity area.
- Module names, checklist IDs, and configuration labels appear only as page titles or content headings.
- Admin, User, HOD, and Management pages use the same rule.

### Step 2: Responsive Header and Table Control QA Fixes

Priority: High

Why second:

- Header consistency changes should be verified across small widths.
- Tables and topbars are the most likely mobile pressure points.

Acceptance:

- Re-run viewport checks at `320`, `375`, `390`, `412`, `768`, and `1024`.
- No hidden primary actions.
- No page-level horizontal overflow except intentional table scroll containers.
- Sidebars remain usable.

### Step 3: Icon Gallery Foundation

Priority: High

Why third:

- It is the largest remaining gap from the UI/UX and Control Panel plans.
- It should be implemented as a safe registry before replacing existing icons.

Acceptance:

- Local icon library packaged.
- Allowlisted registry exists.
- AppSettings stores semantic icon slots.
- Control Panel exposes picker and previews.
- Sidebar consumes icon assignments.
- Raw SVG/HTML cannot be stored.

### Step 4: Icon Migration and Glyph Removal

Priority: Medium

Why fourth:

- Once the registry exists, migrate visible glyphs/emoji/masks incrementally.

Acceptance:

- Sidebar masks replaced by shared icon renderer.
- Bell, search, close, profile-photo, export, approve, reject, settings, logs, and table action icons use one icon system.

### Step 5: Notification Center Enterprise Enhancements

Priority: Medium

Why fifth:

- Phase 1 in-app notification is already working.
- Enterprise features should follow the stable settings/icon foundation.

Recommended order:

1. Configurable popup durations.
2. Test notification button.
3. Notification history page.
4. Event categories.
5. Templates.
6. Role preferences.
7. User preferences.
8. Acknowledgement and delivery history.

### Step 6: CSS Governance Cleanup

Priority: Medium

Why sixth:

- Existing page-local CSS still competes with shared UI.
- Cleanup is safer after header/icon/control requirements stabilize.

Acceptance:

- No new page-level `.btn` or generic table system.
- Shared component styles own cards, buttons, cursors, headers, tables, and modals.

## 4. Risk Assessment

| Work Item | Risk | Details | Mitigation |
|---|---:|---|---|
| Header identity centralization | Low | Mostly template changes, but page titles may need relocation. | Add tests for Admin, User, HOD, Management and checklist preview pages. |
| Responsive topbar cleanup | Medium | Small widths can expose layout regressions across every role. | Use screenshot/geometry checks at the required widths after implementation. |
| Icon Gallery | Medium/High | Unsafe icon storage could introduce XSS or duplicate icon systems. | Store only allowlisted keys; no raw SVG/HTML; add validation tests. |
| Sidebar icon migration | Medium | Navigation icons are visible everywhere and regression-prone. | Implement shared renderer with safe fallbacks before migrating slots. |
| Notification enterprise enhancements | Medium/High | Preferences, templates, and history can duplicate existing notification settings. | Keep `NotificationSetting` authoritative; introduce models only for clearly separate concerns. |
| Notification templates | High | Admin-editable templates can create injection/privacy problems. | Use restricted variables, escaping, no arbitrary Django tags/filters. |
| CSS cleanup | Medium | Removing overrides can alter old screens. | Migrate module by module with visual QA. |
| Full responsive certification | Medium | Requires role-specific data and viewport tests. | Use seeded preview data and automated width checks in a separate implementation cycle. |

## 5. Final Remaining Scope After Completed Upgrades

Already completed or substantially completed:

- Control Panel 2.0 Phase 1.
- Avatar rendering modernization.
- Profile modernization with shared profile content.
- Avatar crop modal UX optimization.
- Universal Table Framework core behavior.
- Notification Control Phase 1.
- Activity Log append-only foundation and workflow coverage.
- Approval comments and immutable decision history.
- HOD approval enforcement.
- Secure uploads and attachment access.
- Geolocation tracking and validation.

Remaining final scope:

1. Header identity consistency across every authenticated page.
2. Full Global Icon Gallery.
3. Migration away from CSS masks, emoji, and text glyph icons.
4. Final mobile responsiveness certification across all requested widths.
5. Notification Center enterprise enhancements beyond Phase 1.
6. CSS governance cleanup to remove remaining page-local component systems.
7. Optional visual regression and accessibility gates.

## 6. Incomplete Items By Master Plan

### 6.1 QCMS_UI_UX_STANDARDIZATION_MASTER_PLAN

Incomplete:

- Global Icon Gallery.
- Lucide/local icon library adoption.
- Replacement of emoji/glyph/search/bell/close icons.
- Full removal of duplicate button/card CSS systems.
- Final visual regression across all roles and required widths.
- Complete accessibility certification at keyboard, reduced-motion, contrast, and 200 percent zoom.

Substantially completed:

- Header avatar and profile fallback.
- Button/cursor/card profile foundations.
- Table action left alignment.
- Notification Control naming.
- Shared table framework.
- Shared profile and avatar system.

### 6.2 QCMS_CONTROL_PANEL_2_0_MASTER_PLAN

Incomplete:

- Icon Gallery section.
- Admin-configurable icon slots.
- Popup duration settings.
- Notification test action.
- Notification history.
- Notification categories.
- Role/user notification preferences.
- Safe notification templates.
- Full cleanup of dormant/legacy settings such as unused notification JSON ownership.

Substantially completed:

- Control Panel section structure.
- Component profiles for card, button, cursor.
- Header controls.
- Table controls.
- Notification Control integration.
- Settings audit logging.
- Existing URL preservation.

### 6.3 QCMS_PROFILE_AND_AVATAR_MASTER_PLAN

Incomplete or partially complete:

- Remove/reset avatar action is still not confirmed implemented.
- Mature cropper-library adoption remains future optional; current custom cropper has been modernized.
- Strict CSP cleanup may still require removing any remaining inline handlers elsewhere.
- Full mobile/touch/keyboard visual certification should remain part of final QA.

Completed:

- Shared avatar renderer.
- Header avatar consistency.
- Profile page modernization.
- Shared profile content.
- Crop modal with explicit zoom, reset, cancel, apply.
- Pointer/drag support, keyboard support, focus trap, escape close, focus restoration.
- Square normalized server-side avatar storage.
- Old avatar replacement cleanup.
- Safe image enhancement before crop.

### 6.4 QCMS_UNIVERSAL_TABLE_FRAMEWORK_PLAN

Incomplete or requiring final QA:

- Full width-specific visual certification for every business grid was interrupted.
- Table sorting is not confirmed uniformly implemented across all modules.
- Active filter chips or concise active-filter summaries are not confirmed implemented.
- Specialized configuration matrices still require final shared settings-table cleanup.
- Export audit logging should be reviewed module by module if not already covered.

Substantially completed:

- Search, filters, clear filters, pagination, page-size selector, and Excel export across core business grids.
- Default page size 25 with 50, 100, and 250 options.
- Complete filtered dataset export before pagination.
- Spreadsheet formula-injection protection.
- Shared pagination and result count.
- Query-string preservation.

### 6.5 NOTIFICATION_CENTER_MASTER_PLAN

Incomplete:

- Categories.
- Notification history/search page.
- Notification templates.
- Test notification button.
- Role-specific preferences.
- User-specific preferences.
- Acknowledgement.
- Delivery history.
- Configurable popup durations.
- Quiet hours/digests.
- SSE/WebSockets.
- Email.
- SLA and escalation.
- External integrations.

Completed for Phase 1:

- Database-backed notifications.
- Recipient-scoped bell and drawer.
- Unread count with `99+`.
- All, Unread, and Action Required filters.
- Polling.
- Mark read, mark all read, delete.
- Related-page navigation.
- Global settings.
- Priority colors.
- Per-event enable, priority, and popup controls.
- High/Critical popup behavior.
- Notification Control Admin page.

## 7. Recommended Final Implementation Scope

Recommended final stabilization scope before declaring UI/UX standardization complete:

1. Header Identity Fix
   - Make `Welcome, <Full Name>` universal.
   - Remove module/context labels from the identity area.

2. Responsive Certification Fixes
   - Run and address the full required width matrix.
   - Focus on topbar, sidebar, tables, Notification Control, Control Panel, Logs, Profile, Checklist, and Response pages.

3. Icon Gallery Phase 1
   - Add local icon registry and Control Panel picker.
   - Support sidebar and key action icons first.

4. Icon Migration Phase 2
   - Replace CSS masks and glyph/emoji icons.
   - Keep safe fallback icons.

5. Notification Control Phase 2
   - Add configurable popup durations and test notification.
   - Add history page and categories.

6. CSS Governance Cleanup
   - Remove remaining duplicate component styling after icon/header work stabilizes.

## 8. Final Readiness Position

QCMS is functionally strong after the completed security, workflow, table, profile, notification, activity-log, geolocation, and Control Panel upgrades.

The remaining readiness blockers are not core business logic blockers. They are enterprise polish and governance blockers:

- Header identity must be made consistent.
- Global Icon Gallery remains the largest unimplemented approved UI feature.
- Final mobile width certification must be completed after the header and icon changes.
- Notification Center still has Phase 2+ enterprise features pending.

Recommended status:

```text
IMPLEMENTATION-READY FOR FINAL UI/UX COMPLETION
```

Do not start Email, SLA, Escalation, WebSocket/SSE, or external integration work until the remaining UI/UX and Control Panel items above are completed.
