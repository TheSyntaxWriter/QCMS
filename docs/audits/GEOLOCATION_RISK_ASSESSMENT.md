# QCMS Geolocation Risk Assessment

## Executive Recommendation

Geolocation should be **configurable through Admin Settings**, with these modes:

1. **Off** - no browser coordinates are requested.
2. **Optional** - recommended default; users may share location, but denial or failure does not block workflow.
3. **Required on Submit** - available only for checklists with a documented operational or compliance need.

Do not make geolocation globally mandatory. Browser permission denial, unavailable device sensors, desktop limitations, indoor signal quality, VPNs, and regional browser behavior would otherwise block legitimate work.

Use **browser geolocation plus server-observed IP context** when enabled. Treat the two sources as independent audit signals, not proof that a person was physically present. Never silently replace denied GPS access with a claim that IP location is equivalent.

## Current QCMS Context

- `ChecklistResponse` stores the workflow state but no location data.
- `ResponseDecision` stores immutable approval and rejection history.
- `ActivityLog` already records server-observed IP address and user agent.
- Draft, submit, approve, and reject are distinct business events.
- `AppSettings` already contains `general_settings`, `security_settings`, and `system_preferences` JSON configuration areas.

Location should therefore be stored as append-only **event evidence**, not mutable latitude/longitude columns on `ChecklistResponse` or `UserProfile`.

## Option Comparison

| Approach | Strengths | Weaknesses | QCMS suitability |
|---|---|---|---|
| Browser/GPS coordinates | Can be precise on sensor-equipped mobile devices; includes an accuracy radius and device timestamp | Requires HTTPS and permission; weak indoors; poor or unavailable on many desktops; client data can be spoofed | Useful when voluntarily captured with accuracy metadata |
| IP-based location | No browser permission prompt; server can capture IP automatically | Often resolves to ISP/VPN/proxy infrastructure; weak on mobile/carrier networks; may be city/region level only | Context and anomaly signal only |
| GPS + IP | Provides two independent signals; can identify large inconsistencies | More personal data, more cost, more failure states; neither source proves presence | Recommended when geolocation is enabled, with explicit source labels |

## 1. Browser Support

The Geolocation API is broadly supported by current major browsers, but it requires a secure HTTPS context and explicit user permission. Permission may be denied, session-limited, time-limited, permanently blocked, or controlled by operating-system settings. Embedded or third-party contexts can also be restricted by `Permissions-Policy`.

Operational implications:

- Production QCMS must use HTTPS.
- Use one-shot `getCurrentPosition()`, not continuous `watchPosition()`.
- Set a finite timeout, such as 8-12 seconds.
- Distinguish `permission_denied`, `position_unavailable`, and `timeout` outcomes.
- Never assume browser support means a usable position will be returned.
- Do not repeatedly prompt after denial; provide settings guidance and a policy-compliant fallback.

## 2. Desktop Accuracy

Desktop and laptop browsers commonly infer location from Wi-Fi/network positioning or IP data. Many desktops have no GPS receiver. Corporate VPNs, remote desktops, virtual machines, wired networks, disabled Wi-Fi, and centralized internet gateways can place a user in another city or region.

Expected behavior:

- Accuracy may range from tens of meters to many kilometres.
- A returned coordinate with a large `accuracy` radius must not pass a site-presence rule.
- Office desktops behind one gateway may all appear at the same location.
- Remote desktop sessions may represent the endpoint device, host device, or network location inconsistently.

Recommendation: accept desktop coordinates only as contextual evidence. Display their accuracy radius and source quality prominently to reviewers.

## 3. Mobile Accuracy

Mobile devices can combine GPS, Wi-Fi, Bluetooth, cell towers, and network signals. Outdoors with precise location enabled, results can be substantially better than desktop results. Indoors, underground, in dense buildings, in battery-saving mode, or with approximate-location settings, accuracy can degrade significantly.

Risks:

- Users can disable precise location and provide only an approximate location.
- First acquisition can be slow or time out.
- Cached positions can be stale unless `maximumAge` is controlled.
- Mobile IP geolocation is particularly unreliable because carrier traffic may exit far from the device.

Recommendation: request high accuracy only for submission events that genuinely require it. Store the browser-reported accuracy and position timestamp, and reject stale client positions rather than silently accepting them.

## 4. Privacy Implications

Precise location is sensitive personal data because it can reveal workplace attendance, movement patterns, customer sites, health or religious visits, and home addresses. Combining it with usernames, projects, departments, timestamps, IP addresses, and checklist content increases sensitivity.

Required governance before rollout:

- Document the business purpose and lawful basis for each location-enabled checklist.
- Show a clear notice before the browser permission prompt.
- Explain whether location is optional or required and what happens after denial.
- Define who may view exact coordinates.
- Define a short retention period based on audit need.
- Provide an access/correction/deletion process where legally applicable, with documented exceptions for immutable regulated audit evidence.
- Do not reuse location for attendance, productivity scoring, disciplinary monitoring, or analytics without a separately approved purpose.
- Do not send coordinates to map, reverse-geocoding, or IP-location providers without reviewing their terms, retention, cross-border processing, and security controls.

The W3C recommends requesting location only when necessary, limiting use to the stated task, protecting stored data, defining retention, and clearly disclosing collection and sharing.

## 5. Database Impact

Storage volume is modest if QCMS captures one record per selected workflow event. The larger concern is sensitivity, retention, access control, and query design.

Recommended append-only model: `ResponseLocationEvent`.

### Core fields

| Field | Purpose |
|---|---|
| `id` | Primary key |
| `response_id` | Related checklist response |
| `decision_id` | Nullable link to the approval/rejection decision |
| `actor_id` | User who performed the event |
| `actor_role` | Role snapshot at capture time |
| `event_type` | `submit`, `approve`, or `reject` |
| `server_captured_at` | Authoritative server timestamp |
| `capture_policy` | Snapshot such as `optional` or `required` |
| `capture_status` | `captured`, `denied`, `timeout`, `unavailable`, `unsupported`, or `not_requested` |
| `consent_notice_version` | Notice/policy version shown to the user |

### Browser-position fields

| Field | Recommendation |
|---|---|
| `latitude` | Nullable decimal, sufficient for WGS84 coordinates |
| `longitude` | Nullable decimal |
| `accuracy_meters` | Required whenever coordinates are present |
| `client_position_timestamp` | Timestamp supplied with the browser position |
| `position_age_ms` | Calculated age at submission |
| `high_accuracy_requested` | Records capture configuration, not actual quality |

Do **not** store altitude, speed, or heading unless a separately approved business requirement exists.

### Network-context fields

| Field | Recommendation |
|---|---|
| `ip_address` | Server-derived address, subject to retention/access policy |
| `forwarded_ip_trusted` | Whether the address came through a configured trusted proxy chain |
| `ip_country_code` | Nullable coarse IP-derived result |
| `ip_region` / `ip_city` | Nullable; label as estimated |
| `ip_latitude` / `ip_longitude` | Nullable provider estimate |
| `ip_accuracy_radius_km` | Required if the provider supplies it |
| `ip_provider` | Provider/database name |
| `ip_database_version` | Supports reproducible audits |
| `gps_ip_distance_km` | Calculated consistency indicator |
| `user_agent` | Device/browser audit context |

Avoid storing a reverse-geocoded street address by default. It adds sensitivity and can imply false precision.

### Indexes

- `(response_id, event_type, server_captured_at)`
- `(actor_id, server_captured_at)`
- `server_captured_at` for retention jobs
- Do not index raw coordinates unless spatial searching is an approved feature.

## 6. User Experience Impact

Mandatory capture can delay or block submission, especially on desktops, restricted corporate devices, weak mobile signals, or after permission denial.

Recommended UX:

- Explain the purpose before triggering the browser prompt.
- Request location only after the user clicks the final workflow action.
- Show `Locating...` with a visible timeout and cancellation path.
- On success, show approximate quality such as `Accuracy: 35 m` rather than asserting an address.
- In optional mode, allow the action to continue after failure and record the failure category.
- In required mode, provide an authorized exception workflow rather than an endless retry loop.
- Do not request continuous/background tracking.
- Do not display exact coordinates broadly in response tables; show them only in restricted audit details.

## 7. Security Implications

Neither GPS nor IP location is strong authentication or tamper-proof evidence.

- Browser coordinates are client-controlled and can be spoofed using developer tools, browser extensions, emulators, rooted devices, or automation.
- VPNs, proxies, carrier NAT, remote desktops, and corporate gateways distort IP location.
- `X-Forwarded-For` must only be trusted when requests pass through known reverse proxies that overwrite untrusted client headers. QCMS currently uses the first forwarded value without an explicit trusted-proxy check, so it should not be treated as authoritative location evidence.
- Exact coordinates increase breach impact and insider-access risk.
- External geolocation/reverse-geocoding APIs introduce credential, availability, cost, and data-sharing risks.

Controls:

- Encrypt transport with HTTPS and restrict location fields by role.
- Keep raw coordinates out of ordinary logs, URLs, analytics, and error reports.
- Validate coordinate ranges, numeric types, accuracy, timestamp age, and event ownership server-side.
- Rate-limit capture/enrichment endpoints.
- Record source and accuracy; never label IP estimates as GPS.
- Treat large GPS/IP distance as a review signal, not automatic fraud proof.
- Include location records in backup, breach-response, retention, and access-audit policies.

## 8. Audit Value

Geolocation can answer: “What location evidence did the device and network report when this event occurred?” It cannot reliably answer: “Was this person physically present at this exact site?”

High-value uses:

- Confirming that a field checklist was plausibly submitted near an expected site.
- Supporting investigation of unusual submissions or remote overrides.
- Demonstrating that a location capture was requested, denied, timed out, or unavailable.
- Comparing browser coordinates with coarse network context.

Low-value or unsafe uses:

- Sole evidence for disciplinary action.
- Automatic rejection based only on IP mismatch.
- Exact attendance tracking.
- Continuous movement history.
- Assuming a small accuracy radius proves the identity of the operator.

## Capture Recommendations by Workflow Event

| Event | Default recommendation | Reason |
|---|---|---|
| Save Draft (WIP) | Do not capture | Drafts may be saved repeatedly; collection adds little audit value and creates movement history |
| Submit | Capture when enabled | This is the primary business attestation and highest-value location event |
| Approve | Optional, Admin-configurable | Useful for regulated/high-risk remote approvals, but usually unnecessary for assigned-HOD workflow |
| Reject | Optional, same policy as approval | Rejection reason and actor identity generally provide more value than location |

Recommended default policy: **optional GPS + automatic server IP context on Submit only**. Enable approval/rejection capture only per checklist type or project where a documented risk assessment justifies it.

## Historical Location Tracking

Track history only as immutable, discrete workflow events. Do not overwrite a response-level “current location,” and do not continuously watch location changes.

Each permitted Submit/Approve/Reject action should create at most one location event containing either:

- successful coordinates and quality metadata, or
- a failure/denial status with no coordinates.

This preserves audit truth without building an unnecessary movement-tracking system. Re-submission after rejection should create a new Submit location event because it is a new attestation.

## Admin Configuration Recommendation

Suggested settings:

```text
geolocation_enabled: false
geolocation_mode: off | optional | required_on_submit
capture_on_submit: true
capture_on_approve: false
capture_on_reject: false
capture_on_wip: false
enable_ip_enrichment: false
maximum_position_age_seconds: 60
capture_timeout_seconds: 10
maximum_accepted_accuracy_meters: null
retention_days: organization-defined
allow_authorized_exception: true
```

Allow checklist- or project-specific overrides only after the global feature is enabled. Record the effective policy on every location event so later Admin changes do not rewrite historical meaning.

## Recommended Decision

**Adopt geolocation only as an Admin-configurable audit enhancement.**

- Default: `Off` until privacy notice, retention, role access, proxy trust, and operational exception processes are approved.
- Normal rollout: `Optional`, Submit only, browser coordinates plus server IP context.
- Mandatory mode: only `Required on Submit`, scoped to specific field checklists with a documented necessity and exception process.
- Never require it for WIP.
- Do not require it for approval/rejection by default.
- Store immutable event history, not continuous location changes.
- Do not use location as authentication or conclusive evidence of presence.

## Sources

- [MDN Geolocation API](https://developer.mozilla.org/en-US/docs/Web/API/Geolocation_API)
- [W3C Geolocation specification and privacy considerations](https://www.w3.org/TR/geolocation/)
- [Google Geolocation API overview](https://developers.google.com/maps/documentation/geolocation/overview)
- [Apple Location Services and precise-location controls](https://support.apple.com/en-us/102647)
