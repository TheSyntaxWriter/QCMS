# QCMS Deep Architecture Analysis (Current)

## Key Findings
- Response lifecycle currently is Submit -> Pending -> Approved/Rejected with a hardcoded toggle path.
- RBAC foundation is solid: row-visibility + per-role column/action visibility.
- Workflow readiness is partial: approvals exist, editable lifecycle and transition governance are incomplete.

## Architecture Map
- Runtime checklist schema uses `ChecklistDefinition`/`ChecklistQuestion`/`ChecklistResponse`/`ChecklistAnswer`.
- Legacy schema `Checklist`/`Section`/`Question` still exists and is also used by preview context, creating dual-schema risk.
- Responses UI uses shared partial `admin_panel/partials/response_table.html` in both admin and user submissions screens.

## Response & Permission Control
- Status is stored in `ChecklistResponse.status` (`Pending`, `Approved`, `Rejected`).
- Role-based table configuration comes from `RolePermission.visible_columns` and `RolePermission.allowed_actions`.
- `responses_for_profile` enforces row-level visibility by role.
- `get_role_permission_config` enforces action scoping and returns effective columns/actions.

## Form / Preview / PDF
- Fill form is interactive and template-specific (`user_panel/checklist_fill.html`).
- Preview/PDF share one DOM/template (`shared/checklist_preview_content.html`) through shared server render utilities.
- Preview is read-only document-oriented; it is not yet response-interactive.

## Duplicate Systems Detected
- Dual checklist schemas (runtime + legacy).
- Action catalogs duplicated in backend constants and frontend JS constants.
- Status assumptions duplicated across filters/charts/actions.
- Action handlers split between admin/user endpoints with overlapping behavior.

## Risk Summary
- High: preview-PDF coupling, dual-schema coupling, lack of state machine transitions.
- Medium: adding new statuses safely across UI and analytics.
- Low: extending role permission JSON storage.

## Workflow Readiness
- WIP/editable lifecycle: low readiness.
- Approve/reject lifecycle: basic readiness.
- Response-aware preview + HOD update loop: partial readiness.

## Recommended Migration Phases
1. Centralize workflow/action policy server-side.
2. Add workflow states with compatibility mappings.
3. Implement editable response lifecycle + ownership guards.
4. Add transition timeline/audit fields.
5. Unify preview/form rendering via shared question viewmodel.
6. Retire/isolate legacy checklist schema.

## Enterprise Readiness Score
- **5.8/10** (good RBAC base, insufficient workflow/state orchestration).
