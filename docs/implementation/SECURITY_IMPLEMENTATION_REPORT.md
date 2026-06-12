# Security Implementation Report

## Branch

Current branch: `codex-critical-security-fixes`

This work has not been merged into `main`.

## Scope Implemented

Implemented the requested critical security fixes:

1. XSS fixes in response modals.
2. File upload validation and restrictions.
3. Production-ready security settings.

In addition, development media serving was restricted to `DEBUG=True` as part of production hardening.

## 1. XSS Fixes

### Problem

Response detail modals rendered server-provided checklist and answer data with `innerHTML`. Since checklist questions and answer text are user/admin-controlled content, a malicious value could execute JavaScript in another user's browser.

### Changes

Updated modal rendering to use DOM APIs and `textContent`.

Files changed:

- `frontend/static/admin_panel/admin_responses.js`
- `frontend/static/user_panel/my_submissions.js`

### Security Behavior

- Checklist ID, checklist name, questions, and answers are inserted as text, not HTML.
- File links are created only after URL parsing.
- File URLs must resolve to the same origin.
- File links use `rel="noopener noreferrer"` when opened in a new tab.

## 2. File Upload Validation and Restrictions

### Problem

Checklist file uploads and image uploads were accepted with minimal validation. This allowed risky file types and oversized payloads.

### Changes

Added a dedicated validation module:

- `backend/upload_validation.py`

Validation now covers:

- Checklist attachment extension.
- Checklist attachment content type.
- Checklist attachment size.
- Profile image data URL MIME type.
- Profile image decoded size.
- Profile image content validation through Pillow.
- Branding image extension/content type/size/content validation.

Files changed:

- `backend/upload_validation.py`
- `backend/views/user_panel.py`
- `backend/views/admin.py`
- `backend/tests.py`

### Checklist Attachment Policy

Maximum size: 10 MB.

Allowed extensions and content types:

- `.pdf` - `application/pdf`
- `.png` - `image/png`
- `.jpg`, `.jpeg` - `image/jpeg`
- `.webp` - `image/webp`
- `.txt` - `text/plain`
- `.csv` - `text/csv`, `application/csv`, `text/plain`
- `.doc` - `application/msword`
- `.docx` - `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- `.xls` - `application/vnd.ms-excel`
- `.xlsx` - `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

Blocked examples:

- HTML
- SVG
- JavaScript
- Unknown extensions
- Files with mismatched content type
- Files larger than 10 MB

### Profile Image Policy

Maximum size: 2 MB.

Allowed declared MIME types:

- `image/png`
- `image/jpeg`
- `image/webp`

All profile images are validated and converted to JPEG before saving.

### Branding Image Policy

Maximum size: 2 MB.

Allowed extensions:

- `.png`
- `.jpg`
- `.jpeg`
- `.webp`
- `.ico`

SVG branding uploads are no longer accepted.

## 3. Production-Ready Security Settings

### Problem

The settings file contained development-only defaults:

- Hardcoded insecure secret key.
- `DEBUG=True`.
- Empty `ALLOWED_HOSTS`.
- No production security controls.

### Changes

Updated `qcms/settings.py` to support environment-driven configuration.

New environment variables:

- `DJANGO_DEBUG`
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_SECURE_SSL_REDIRECT`
- `DJANGO_SESSION_COOKIE_SECURE`
- `DJANGO_CSRF_COOKIE_SECURE`
- `DJANGO_SECURE_HSTS_SECONDS`
- `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS`
- `DJANGO_SECURE_HSTS_PRELOAD`
- `DJANGO_X_FRAME_OPTIONS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`

Production behavior:

- `DJANGO_SECRET_KEY` is required when `DJANGO_DEBUG=false`.
- Secure cookies default to enabled when `DEBUG=False`.
- SSL redirect defaults to enabled when `DEBUG=False`.
- HSTS defaults to one year when `DEBUG=False`.
- `SECURE_CONTENT_TYPE_NOSNIFF=True`.
- `X_FRAME_OPTIONS='DENY'` by default.

Local development behavior:

- `DJANGO_DEBUG` defaults to `true`.
- A development-only fallback secret is provided for local use.
- `ALLOWED_HOSTS` defaults to `localhost`, `127.0.0.1`, and `testserver`.

## 4. Development Media Serving Hardening

### Problem

`qcms/urls.py` served media files unconditionally.

### Change

Media files are now served by Django only when `settings.DEBUG` is true.

File changed:

- `qcms/urls.py`

Production note:

- Production media should be served by a controlled web server, object storage, or authenticated download views.

## Tests Added/Updated

Added upload validation tests:

- HTML checklist upload is rejected.
- PDF checklist upload is accepted.

Updated stale tests to reflect current routing/content behavior:

- Non-admin admin-page redirects go to `home` first.
- Legacy admin create route redirects to `/admin-create/`.
- Checklist preview contains `Quality Control Management System`.

File changed:

- `backend/tests.py`

## Verification

### Django System Check

Command:

```bash
python manage.py check
```

Result:

```text
System check identified no issues (0 silenced).
```

### Django Test Suite

Command:

```bash
python manage.py test
```

Result:

```text
Ran 10 tests
OK
```

Note:

- The test run emitted Windows GLib/GIO warnings from local UWP application registrations. These warnings did not fail the test suite.

### Production-Style Deployment Check

Command:

```powershell
$env:DJANGO_DEBUG='false'
$env:DJANGO_SECRET_KEY='production-check-secret-key-with-more-than-fifty-characters-for-validation'
$env:DJANGO_ALLOWED_HOSTS='qcms.example.com'
python manage.py check --deploy
```

Result:

```text
System check identified no issues (0 silenced).
```

## Files Changed

- `qcms/settings.py`
- `qcms/urls.py`
- `backend/upload_validation.py`
- `backend/views/user_panel.py`
- `backend/views/admin.py`
- `backend/tests.py`
- `frontend/static/admin_panel/admin_responses.js`
- `frontend/static/user_panel/my_submissions.js`
- `docs/SECURITY_IMPLEMENTATION_REPORT.md`

## Remaining Security Recommendations

These are important but outside the requested implementation scope:

- Add authenticated download views for checklist answer files.
- Add login rate limiting and account lockout.
- Add Content Security Policy headers.
- Self-host or add integrity controls for external CDN assets.
- Add malware scanning for uploaded files if required by enterprise policy.
- Add full audit events for rejected upload attempts.
