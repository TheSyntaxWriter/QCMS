# QCMS Activity Log Coverage Audit

## 1. Purpose and Scope

This document audits the current QCMS activity logging implementation across user, HOD, Management, Admin, Notification Control, approval, geolocation, settings, upload, and security workflows.

The review is based on the current application code, principally:

- `backend/models.py`
- `backend/logging_service.py`
- `backend/middleware.py`
- `backend/notification_service.py`
- `backend/views/auth.py`
- `backend/views/user_panel.py`
- `backend/views/admin.py`
- `backend/views/notifications.py`
- `backend/permission_service.py`
- `backend/tests.py`

This is a coverage and architecture audit only. No application code was changed.

## 2. Executive Summary

QCMS has a useful centralized `ActivityLog` model and a shared `write_activity_log()` helper. Authentication, profile security, checklist CRUD, checklist submission, master-data administration, user administration, permission changes, and Notification Control settings have partial coverage.

Coverage is nevertheless incomplete for the application's highest-value evidence:

1. `ActivityLog` records are not append-only and can be changed or deleted through ORM operations or scripts.
2. HOD and Management approval/rejection actions create protected `ResponseDecision` history but are not written to `ActivityLog`; equivalent Admin decisions are logged.
3. Control Panel changes, including geolocation enablement, branding, theme, and reset operations, are not logged.
4. Sensitive attachment downloads and denied attachment access are not logged.
5. Suspicious upload rejection, geolocation failure, missing HOD assignment, permission-denial threshold, and protected-history deletion attempts may create notifications but do not consistently create durable security audit events.
6. Most administrative events contain only free-text descriptions. Target object identity, old values, new values, reason, outcome, and correlation data are generally absent.
7. The client-controlled `X-Forwarded-For` header is trusted without an application-level trusted-proxy boundary, weakening IP evidence.
8. Activity logging behavior has almost no direct regression test coverage.

The present implementation is suitable as an operational activity feed, but it is not yet a tamper-resistant or complete enterprise audit trail.

## 3. Audit Standard

### 3.1 Severity definitions

| Severity | Meaning |
|---|---|
| Critical | Evidence can be altered or destroyed, or a material compliance/security investigation can be defeated. |
| High | A privileged, security-sensitive, or workflow-defining action lacks reliable centralized evidence. |
| Medium | Important operational context is absent, inconsistent, or difficult to investigate. |
| Low | Taxonomy, usability, or lower-risk completeness issue with limited immediate business impact. |

### 3.2 What should be audited

Audit coverage should focus on material events, not every click. A durable event is expected for:

- Authentication and account-security outcomes.
- Authorization failures and suspicious behavior.
- Creation, change, activation, deactivation, assignment, and deletion of business records.
- Checklist submission and every workflow status decision.
- Access to sensitive attachments or precise location data.
- Permission, security, retention, notification, and Control Panel configuration changes.
- Attempts to alter or delete protected history.
- System jobs that remove or materially transform records.

Routine dashboard viewing, notification polling, pagination, and ordinary search do not need per-request audit events unless required by policy.

## 4. Current Activity Log Architecture

### 4.1 Data captured

`ActivityLog` currently stores:

- Actor user, role, department, and project.
- Free-text action type and module name.
- Free-text description.
- IP address and user agent.
- Outcome status: `Success`, `Failed`, or `Info`.
- Optional `old_data` and `new_data` JSON.
- Timestamp.

Indexes support common filtering by module/action, user/time, department/project/time, status, IP, and timestamp.

### 4.2 Logging path

`RequestTrackingMiddleware` places the current request in a `ContextVar`. `write_activity_log()` then derives actor context, IP address, and user agent before creating an `ActivityLog` row.

`record_permission_denied()` bypasses the helper and writes a smaller security event directly. Consequently, permission-denied events omit request IP and user agent even when a request exists.

### 4.3 Architectural limitations

- No immutable manager, model protection, delete protection, or database-level append-only control exists for `ActivityLog`.
- No stable machine event key, target object type, target object ID, request/correlation ID, severity, or source channel exists.
- `old_data` and `new_data` are available but current application writes do not populate them.
- Logging is manually invoked in views; model, service, and script changes can bypass it.
- Logging is not consistently coordinated with `transaction.on_commit()`.
- Request context is set but not explicitly reset after a response.
- IP extraction trusts the first `X-Forwarded-For` value without verifying a trusted reverse proxy.
- There is no explicit retention policy, archive strategy, integrity hash, or external immutable sink.

## 5. Actions Currently Logged

| Area | Current event | Coverage notes |
|---|---|---|
| Authentication | Login Success | Actor context, IP, and user agent are captured. |
| Authentication | Login Failure | Username is included in description; actor is normally null. |
| Authentication | Logout | Logged before logout completes. |
| Profile | Profile Image Update | Success, invalid payload, and validation failure are logged. |
| Profile | Password Change Attempt | Incorrect current password and password-policy failure are logged. |
| Profile | Password Changed | Successful self-service change is logged. |
| Checklist | Checklist WIP Saved | User/HOD/Management draft saves are logged. |
| Checklist | Checklist Submitted | Initial submission and rejected-response resubmission share the same activity event. |
| Checklist | Checklist Viewed | Checklist definition preview is logged for Admin and other roles. |
| Checklist | Checklist Printed | Opening print mode is logged. |
| Checklist | Checklist PDF Downloaded | Checklist definition PDF download is logged. |
| Checklist administration | Checklist Created | Successful Admin creation is logged. |
| Checklist administration | Checklist Updated | Successful edit and active-state toggle use this event. |
| Checklist administration | Checklist Deleted | Successful deletion is logged. |
| Response administration | Response Approved / Rejected | Admin override decisions are logged; comment and status transition are omitted. |
| Response administration | Response Deleted | Successful Admin deletion is logged. |
| Users | User Created | Successful Admin creation is logged. |
| Users | User Updated | Profile edits and activation toggles share this event. |
| Users | User Deleted | Successful deletion is logged. |
| Departments | Department Changes | Create, update, and delete share one action type. |
| Projects | Project Changes | Create, update, and delete share one action type. |
| Permissions | Permission Changes | Successful role-permission save is logged without before/after values. |
| Notification Control | Notification Settings Changed | Successful settings save is logged without configuration deltas. |
| Security | Permission Denied | Explicit response-action denials are logged, but without request IP/user agent. |

## 6. Findings by Severity

## Critical

### C-01: ActivityLog history is mutable and deletable

`ActivityLog` has no append-only protections comparable to `ResponseDecision`. Any code with ORM access can call `update()` or `delete()`, and scripts or privileged database access can rewrite evidence. The model is not exposed in the current Django Admin registration, which reduces accidental UI changes, but does not establish immutability.

**Impact:** An attacker, compromised administrator process, faulty maintenance script, or future feature can alter or erase the evidence used to investigate approvals, account activity, and security incidents.

**Recommendation:** Make application-level history append-only; remove change/delete paths; use a restricted database role; add database protection where supported; define controlled retention/archive operations; and consider hash chaining or an external write-once log sink for high-assurance deployments.

## High

### H-01: HOD and Management decisions are absent from ActivityLog

HOD and Management approve/reject actions update `ChecklistResponse` and create immutable `ResponseDecision` records, but do not call `write_activity_log()`. Admin approve/reject actions do. The decision history therefore preserves the business decision, but the centralized Activity Log is role-inconsistent and lacks request IP/user-agent evidence for HOD and Management decisions.

**Recommendation:** Emit distinct `response.approved`, `response.rejected`, `response.override_approved`, and `response.override_rejected` events after a successful transaction. Reference the response and decision IDs, actor role, previous/new status, and whether a comment was supplied. Do not copy sensitive comment text into the general activity log.

### H-02: Control Panel and security-setting changes are not logged

Control Panel save and reset operations can change application identity, theme, branding files, and `geolocation_tracking_enabled`. Failed password confirmation and rejected branding uploads are also unlogged.

**Impact:** Administrators can enable location collection, replace trusted branding, or reset global settings without a durable Activity Log record.

**Recommendation:** Log successful save/reset with redacted before/after deltas, plus failed confirmation and rejected upload outcomes. Use separate event keys for security, branding, and appearance changes.

### H-03: Protected-history attacks are notified but not durably logged

An attempt to delete a response with `ResponseDecision` history creates `protected_audit_action_blocked` notifications, but no `ActivityLog` security event. Notifications are user-deletable and retention-purged, so they are not a substitute for audit evidence.

**Recommendation:** Record `security.protected_history_change_blocked` synchronously with actor, target response, attempted operation, request evidence, and failed outcome.

### H-04: Sensitive attachment access has no audit trail

Authorized checklist attachment downloads and denied attempts are not logged. Denied access returns `404`, which is appropriate for information hiding, but leaves no security record.

**Impact:** QCMS cannot reliably determine who accessed an uploaded document or detect probing of attachment identifiers.

**Recommendation:** Record successful downloads and denied attempts, including answer/response identifiers, actor, file category, and outcome. Do not log storage paths, file contents, or signed URLs.

### H-05: Security notifications are not equivalent to security logs

The following events may create notifications but do not consistently create Activity Log records:

- Suspicious upload rejected.
- Permission denied threshold reached.
- Geolocation capture failed.
- Missing HOD assignment detected.
- Protected audit action blocked.

Notifications can be disabled, individually deleted, or automatically purged. Security evidence must be generated independently of notification preferences.

### H-06: Audit IP addresses can be spoofed through X-Forwarded-For

`get_request_ip()` accepts the first `HTTP_X_FORWARDED_FOR` value whenever present. Unless the deployment edge always strips untrusted forwarding headers, a client can influence the stored audit IP.

**Recommendation:** Trust forwarding headers only from configured proxies, normalize the chain at the edge, and preserve both trusted client IP and immediate peer IP where required.

### H-07: Privileged changes lack target identity and before/after evidence

User role, HOD assignment, department, project, active state, password reset, role permissions, checklist configuration, and Notification Control settings are logged only through broad free-text events. `old_data` and `new_data` are not populated.

**Impact:** Investigators can see that an object changed but often cannot prove exactly what changed, which user was affected after deletion, or whether access was expanded.

**Recommendation:** Add stable target references and redacted field-level deltas. Never log passwords, password hashes, upload contents, approval comment text, or exact coordinates in generic audit metadata.

### H-08: Logging and business transactions can diverge

Manual log calls occur at different points relative to state changes. For example, response deletion is logged before deletion, while many other events are logged after saves. A log database failure can also turn a successful business change into an HTTP error after the change has committed.

**Recommendation:** Define one transaction policy: write required audit records in the same atomic transaction where feasible, and dispatch external copies with `transaction.on_commit()`. Failed business operations must never be logged as successful.

## Medium

### M-01: Notification lifecycle actions are not logged

Notification creation/suppression, mark-read, mark-all-read, delete, popup display, and retention purge are not audited. Logging every read would create noise, but deletions, bulk state changes, settings changes, test notifications, and retention purges are operationally significant.

### M-02: Resubmission is indistinguishable from initial submission

Both paths use `Checklist Submitted` in ActivityLog even though notifications distinguish `checklist_submitted` and `checklist_resubmitted`.

### M-03: Missing HOD assignment changes are not explicit audit events

User edits generate a generic `User Updated` event. Assignment and removal notifications exist, but the centralized log does not identify previous and new HODs or record the high-risk condition where a normal User has no valid assigned HOD.

### M-04: Geolocation lifecycle coverage is incomplete

Successful submit-time capture, permission denial/unavailability, malformed coordinate rejection, and geolocation setting changes are not represented by structured audit events. Exact coordinates should remain on the authorized response record rather than being duplicated into ActivityLog.

### M-05: Many failed administrative actions are silent

Duplicate usernames/codes, invalid permission payloads, invalid domains, failed form validation, invalid rejection requests, blocked workflow transitions, and missing targets generally produce UI errors without a corresponding failed activity event.

Only security-relevant or repeated failures should be logged to avoid noise. Permission, protected-history, upload, authentication, and privileged-setting failures should be mandatory.

### M-06: Viewing activity logs is not itself audited

Admin access to the Activity Log page is not recorded. There is currently no Activity Log export, but future export/download operations must be logged because logs contain IP addresses, account activity, and security evidence.

### M-07: Request context is not explicitly reset

`RequestTrackingMiddleware` sets a `ContextVar` but does not reset its token in `finally`. This can preserve stale request context in reused execution contexts or nonstandard async/background flows.

### M-08: No central event catalog or enforced schema exists

Free-text action names such as `Department Changes`, `Project Changes`, and `User Updated` combine different operations. Event names can drift, and reports cannot safely infer operation type from descriptions.

### M-09: Activity logging lacks regression tests

Tests create ActivityLog fixtures for list rendering, but do not assert that key business and security actions generate correct immutable events, target references, outcomes, or deltas.

## Low

### L-01: Read/download coverage is inconsistent

Checklist definition views, print previews, and PDFs are logged, while response-detail views and attachment downloads are not. A data-classification policy should determine which reads are audit-worthy.

### L-02: Password confirmation mismatch is not logged

Incorrect current passwords and password-policy failures are logged, but new-password confirmation mismatch is not. This is low risk unless repeated mismatches are used as an anomaly signal.

### L-03: Management has no distinct operational event namespace

Management uses shared dashboard and response views. Its override actions should be identifiable through stable event keys rather than inferred from actor role and free text.

### L-04: Log descriptions may become inconsistent after target deletion

Target identity is embedded in descriptions rather than preserved in dedicated immutable fields. Names can be ambiguous, renamed, or unavailable after deletion.

## 7. Missing Events Matrix

| Area | Missing or incomplete event | Current evidence elsewhere | Severity | Minimum metadata |
|---|---|---|---|---|
| Audit integrity | Activity log modified/deleted/retention purge | None | Critical | actor/process, operation, affected range/count, reason |
| HOD approval | Approve response | `ResponseDecision` | High | response ID, decision ID, old/new status, actor role |
| HOD rejection | Reject response | `ResponseDecision` | High | response ID, decision ID, old/new status, reason-present flag |
| Management | Override approve/reject | `ResponseDecision`, notification | High | response/decision IDs, override flag, old/new status |
| Admin | Override approve/reject details | Coarse ActivityLog row | High | target, decision ID, status delta, override flag |
| Security settings | Geolocation enabled/disabled | `AppSettings.updated_at` only | High | old/new boolean, actor, target settings ID |
| Control Panel | Settings saved/reset | UI message only | High | changed field names, redacted deltas, operation |
| Branding | Logo/favicon accepted or rejected | Stored file/UI message | High | field, validation outcome, file type/size, no path/content |
| Attachments | Authorized download | HTTP response only | High | answer/response ID, actor, outcome |
| Attachments | Unauthorized download attempt | Concealed `404` only | High | requested ID, actor, peer/client IP, failed outcome |
| Upload security | Suspicious upload rejected | Notification | High | checklist/question, rejection class, file type/size |
| Security | Permission threshold reached | Notification plus individual denials | High | actor, count, time window, threshold |
| Security | Protected response/history deletion blocked | Notification | High | response ID, attempted operation, actor |
| Permissions | Role permission changed | Coarse ActivityLog row | High | role, old/new columns/actions/projects |
| User administration | Role changed | Generic `User Updated` | High | target user, old/new role |
| User administration | HOD assigned/removed | Notification, generic update | High | target user, previous/new HOD IDs |
| User administration | Admin reset user password | Generic `User Updated` | High | target user, password-changed flag only |
| User administration | Activated/deactivated | Generic `User Updated`; deactivation notification | Medium | target user, old/new state |
| Workflow | Rejected response resubmitted | Generic `Checklist Submitted`, notification | Medium | response ID, old/new status, attempt sequence |
| Workflow | Blocked transition | HTTP error; some permission denials | Medium | action, status, policy reason, actor |
| Geolocation | Capture succeeded/unavailable/invalid | Response fields or notification | Medium | response ID, capture outcome; no coordinates |
| HOD governance | Missing/invalid assigned HOD | Notifications | Medium | user/response ID, validation reason |
| Notifications | Settings changed with deltas | Coarse ActivityLog row | Medium | redacted old/new settings |
| Notifications | Notification deleted | None | Medium | notification ID/event key, recipient/actor |
| Notifications | Mark all read | None | Low | actor, affected count |
| Notifications | Retention purge | Delete count only returned internally | Medium | cutoff, deleted count, job/request identity |
| Notifications | Event suppressed by settings | None | Low | aggregate event key/count; avoid one row per suppression |
| Logs | Activity Log viewed | None | Medium | actor, filter summary, no search secrets |
| Logs | Activity Log exported | Not implemented | High when introduced | actor, filters, result count, format |
| Checklist admin | Active state changed | Generic `Checklist Updated` | Medium | checklist ID, old/new active state |
| Checklist admin | Questions added/changed/removed | Generic checklist event | Medium | checklist ID, question IDs/counts, redacted delta |
| Master data | Department create/update/delete | Generic `Department Changes` | Medium | target ID, operation, old/new values |
| Master data | Project create/update/delete | Generic `Project Changes` | Medium | target ID, operation, old/new values |
| Response | Response detail viewed | None | Low/Medium | response ID, actor, data class |
| Authentication | Session expiration/forced logout | None | Low/Medium | user, reason, session identifier hash |

## 8. Recommended Event Catalog

Use stable lowercase machine keys. Human labels and descriptions should be presentation fields, not the event identity.

### 8.1 Authentication and profile

| Event key | Default outcome/severity | Required context |
|---|---|---|
| `auth.login_succeeded` | Success / Medium | actor, IP, user agent, session ID hash |
| `auth.login_failed` | Failed / High | attempted username, IP, user agent, reason class |
| `auth.logout` | Success / Low | actor, session ID hash |
| `auth.password_changed` | Success / High | actor, self/admin source; never password data |
| `auth.password_change_failed` | Failed / Medium | actor, reason class |
| `profile.image_updated` | Success / Low | actor, validation metadata |
| `profile.image_rejected` | Failed / Medium | actor, rejection class |

### 8.2 Checklist and response workflow

| Event key | Default outcome/severity | Required context |
|---|---|---|
| `checklist.created` | Success / Medium | checklist ID, creator, initial scope |
| `checklist.updated` | Success / Medium | checklist ID, redacted delta |
| `checklist.activation_changed` | Success / Medium | checklist ID, old/new state |
| `checklist.deleted` | Success / High | checklist ID/business key, dependent counts |
| `checklist.draft_saved` | Success / Low | response/checklist IDs |
| `checklist.submitted` | Success / Medium | response/checklist IDs, old/new status |
| `checklist.resubmitted` | Success / High | response ID, prior rejection decision ID |
| `response.viewed` | Info / Low | response ID, actor, view source |
| `response.approved` | Success / High | response/decision IDs, HOD actor, status delta |
| `response.rejected` | Success / High | response/decision IDs, HOD actor, reason-present flag |
| `response.override_approved` | Success / Critical | response/decision IDs, Admin/Management actor, status delta |
| `response.override_rejected` | Success / Critical | response/decision IDs, Admin/Management actor, reason-present flag |
| `response.transition_blocked` | Failed / High | response ID, requested action, current status, policy reason |
| `response.deleted` | Success / Critical | response ID, actor, reason, dependent counts |
| `response.protected_delete_blocked` | Failed / Critical | response ID, actor, decision count |

### 8.3 User, role, and master-data administration

| Event key | Default outcome/severity | Required context |
|---|---|---|
| `user.created` | Success / High | target user ID, role, department/project IDs |
| `user.updated` | Success / Medium | target user ID, redacted delta |
| `user.role_changed` | Success / Critical | target user ID, old/new role |
| `user.activation_changed` | Success / High | target user ID, old/new state |
| `user.deleted` | Success / Critical | immutable target ID/username, actor, reason |
| `user.hod_assigned` | Success / High | user ID, previous/new HOD IDs |
| `user.hod_removed` | Success / High | user ID, previous HOD ID |
| `user.hod_missing_detected` | Failed / High | user/response ID, detection source |
| `permission.role_configuration_changed` | Success / Critical | role, old/new allowlisted configuration |
| `department.created/updated/deleted` | Success / Medium-High | target ID, operation-specific delta |
| `project.created/updated/deleted` | Success / Medium-High | target ID, operation-specific delta |

### 8.4 Settings and Notification Control

| Event key | Default outcome/severity | Required context |
|---|---|---|
| `settings.control_panel_changed` | Success / High | changed field names and redacted deltas |
| `settings.control_panel_reset` | Success / Critical | actor, affected sections |
| `settings.confirmation_failed` | Failed / High | actor, operation attempted |
| `settings.branding_changed` | Success / Medium | logo/favicon field and validation metadata |
| `settings.branding_upload_rejected` | Failed / High | rejection class, type, size |
| `settings.geolocation_changed` | Success / Critical | old/new enabled state |
| `notification.settings_changed` | Success / High | changed settings/event keys, redacted deltas |
| `notification.deleted` | Success / Medium | notification ID, event key, actor/recipient |
| `notification.bulk_marked_read` | Success / Low | actor, affected count |
| `notification.retention_purged` | Success / High | cutoff, deleted count, initiator/job ID |
| `notification.test_sent` | Success/Failed / Medium | actor, recipients/count |

### 8.5 Security, upload, geolocation, and audit access

| Event key | Default outcome/severity | Required context |
|---|---|---|
| `security.permission_denied` | Failed / High | actor, requested action, target, IP/user agent |
| `security.permission_threshold_reached` | Failed / Critical | actor, count/window/threshold |
| `security.upload_rejected` | Failed / High | target question, type/size, rejection class |
| `security.attachment_access_denied` | Failed / Critical | actor, requested answer/response ID |
| `security.protected_history_change_blocked` | Failed / Critical | actor, target, attempted ORM/UI operation |
| `attachment.downloaded` | Success / High | actor, answer/response ID, classification |
| `geolocation.capture_succeeded` | Success / Medium | response ID, accuracy band only if needed |
| `geolocation.capture_unavailable` | Info / Low | response ID, denied/unavailable category |
| `geolocation.capture_invalid` | Failed / High | response ID/request context, validation category |
| `audit.log_viewed` | Info / Medium | actor, filter category |
| `audit.log_exported` | Success / Critical | actor, filters, row count, format |
| `audit.retention_executed` | Success / Critical | cutoff, count, policy/version |
| `audit.integrity_check_failed` | Failed / Critical | range/check identifier, failure summary |

## 9. Recommended Audit Record Contract

Every material event should carry a consistent schema:

| Field | Recommendation |
|---|---|
| Event key | Stable machine key from a controlled catalog. |
| Event version | Allows future schema evolution without changing meaning. |
| Actor | User ID plus role snapshot; support a system/service actor. |
| Target | Object type, immutable object ID, and safe business key snapshot. |
| Outcome | Success, failed, blocked, or informational. |
| Risk/severity | Separate from outcome. |
| Timestamp | Server-generated UTC timestamp. |
| Request evidence | Trusted client IP, peer IP, user agent, request/correlation ID. |
| Change delta | Redacted old/new values for allowlisted fields. |
| Reason | Controlled reason code plus short safe summary. |
| Source | UI, API, admin, scheduled job, migration, or script. |
| Related records | Response decision, checklist, notification, or settings IDs as applicable. |

Sensitive values that should not be copied into ActivityLog include passwords, password hashes, session secrets, CSRF tokens, complete file paths, file contents, approval/rejection comment text, and exact latitude/longitude. Store references and presence/category flags instead.

## 10. Priority Order

1. Protect ActivityLog from ordinary update/delete operations and define controlled retention.
2. Add centralized events for all HOD, Management, and Admin decisions.
3. Log permission changes, role changes, HOD assignment changes, and protected-history attacks with target IDs and deltas.
4. Log Control Panel changes, geolocation enablement, branding changes, resets, and failed confirmations.
5. Log suspicious upload rejection and attachment access/denial.
6. Separate security logging from notification delivery and settings.
7. Correct trusted-proxy IP handling and include request evidence in all security events.
8. Introduce a stable event catalog and structured target/delta fields.
9. Add retention-purge, audit-view, and future audit-export events.
10. Add regression, immutability, transaction, and authorization tests.

## 11. Implementation Phases

### Phase 0: Audit integrity foundation

- Make ActivityLog append-only in intended application paths.
- Prohibit normal Django Admin, manager, queryset, and instance update/delete operations.
- Define a privileged, explicit retention/archive service rather than unrestricted deletion.
- Add stable event key, event version, target type/ID, request ID, source, and severity fields.
- Establish trusted-proxy IP extraction and reset request context in middleware.
- Define redaction rules and a machine-readable event catalog.
- Add tests for immutability, request context, IP derivation, and event schema.

### Phase 1: Workflow and security coverage

- Audit HOD approvals/rejections and Management/Admin overrides.
- Audit blocked transitions and protected-history deletion attempts.
- Audit permission denials with complete request context and threshold events.
- Audit suspicious upload rejection and attachment download/access denial.
- Preserve `ResponseDecision` as the authoritative decision history and link ActivityLog events to it.

### Phase 2: Privileged administration and settings

- Split generic user events into role, status, HOD assignment, password-reset, and profile-change events.
- Capture allowlisted before/after values for role permissions.
- Audit Control Panel save/reset, geolocation enablement, and branding validation outcomes.
- Split project, department, and checklist events by create/update/activation/delete operation.

### Phase 3: Notification, geolocation, and operational lifecycle

- Audit notification settings deltas, notification deletion, bulk read, test sends, and retention purge.
- Add structured geolocation capture outcome events without duplicating exact coordinates.
- Audit missing-HOD detection as a governance event independent of notification delivery.
- Add Activity Log view and future export events.

### Phase 4: Enterprise assurance and scale

- Add log retention tiers, archive verification, and legal-hold procedures.
- Forward Critical/High events to an external security or immutable log sink.
- Add integrity checks or hash chaining where audit assurance requirements justify it.
- Add correlation IDs across activity events, notifications, responses, and decisions.
- Add anomaly reports for repeated denials, upload attacks, unusual exports, and privileged setting changes.
- Monitor logging failures and alert without silently losing required evidence.

## 12. Testing Strategy

Minimum automated coverage should prove:

- Each cataloged material action creates exactly one correct event after success.
- Failed or rolled-back actions do not create success events.
- HOD, Management, and Admin decisions link to the correct `ResponseDecision`.
- Unauthorized and protected-history operations create failed security events.
- ActivityLog rows cannot be edited or deleted through intended ORM/Admin paths.
- Redacted deltas never expose secrets, comment text, file content, or coordinates.
- Notification disablement does not disable security audit events.
- Trusted proxy handling rejects spoofed forwarding chains.
- Retention jobs record cutoff, policy, and deleted/archived counts.
- Actor role, department, and project are stored as event-time snapshots.

## 13. Acceptance Criteria for Complete Coverage

QCMS should be considered enterprise-ready for activity auditing when:

1. Every privileged state change and workflow decision has a stable, structured event.
2. Security evidence is independent of notifications and UI messages.
3. Activity records are append-only outside a documented retention process.
4. Target identity and allowlisted before/after values survive target deletion or renaming.
5. IP and request evidence follow a documented trusted-proxy model.
6. Sensitive values are consistently redacted.
7. Required events are transactionally consistent with business outcomes.
8. Automated tests cover event presence, absence, immutability, authorization, and redaction.
9. Retention, archive, export, and integrity-check operations are themselves audited.
10. Critical events can be monitored independently of the primary application database.

## 14. Final Assessment

The existing Activity Log provides a good base for operational visibility, particularly around authentication, checklist administration, user administration, and basic submissions. Its strongest complementary control is the immutable `ResponseDecision` history.

The immediate concern is not merely the number of missing events. The integrity and structure of the audit record must be strengthened first. After that foundation, the highest business value comes from complete approval/override coverage, privileged settings and permission changes, attachment access, upload/security failures, and protected-history attempts.

Until the Critical and High findings are addressed, QCMS Activity Log data should not be treated as a complete or tamper-resistant system of record for compliance, forensic investigation, or non-repudiation.
