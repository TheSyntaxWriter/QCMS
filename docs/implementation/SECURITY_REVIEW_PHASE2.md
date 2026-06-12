# Security Review Phase 2

## Branch

Current branch: `codex-critical-security-fixes`

This work remains unmerged from `main`.

## Scope

This phase addressed the remaining High severity findings from the post-implementation security review:

1. Upload validation still relied too heavily on client-provided content type.
2. Response JSON still exposed direct `answer.file.url` media links instead of permission-checked download endpoints.

## Upload Validation Hardening

### Implemented

Updated `backend/upload_validation.py` to validate file content, not only extension and client-provided `Content-Type`.

Validation now includes:

- PDF signature check with `%PDF-`.
- PDF readability check through `pypdf.PdfReader`.
- PNG/JPG/WEBP image validation through Pillow.
- TXT/CSV UTF-8 text decoding.
- TXT/CSV rejection when early content contains HTML/script markers.
- DOC/XLS legacy Office OLE compound-file magic byte validation.
- DOCX/XLSX ZIP validation with expected Office package entries.
- Existing size and extension restrictions remain in place.

### Files impacted

- `backend/upload_validation.py`
- `backend/views/user_panel.py`
- `backend/views/admin.py`
- `backend/tests.py`

### Security impact

Spoofed uploads such as `payload.pdf` containing HTML/script content are now rejected. Office and image formats must also match expected container/content structure.

## Secure Attachment Access

### Implemented

Added an authenticated checklist-answer attachment download endpoint:

```text
/attachments/checklist-answers/<answer_id>/
```

Route name:

```text
checklist_answer_download
```

Download authorization:

- Anonymous users are redirected to login.
- Admin users can download attachments for all responses.
- User, HOD, and Management downloads are allowed only if the parent response is visible through the existing `responses_for_profile` role-scope service.
- Unauthorized or missing attachments return 404 to avoid leaking attachment existence.

Response hardening:

- `X-Content-Type-Options: nosniff`
- `Content-Security-Policy: default-src 'none'; sandbox`

### Files impacted

- `backend/urls.py`
- `backend/views/__init__.py`
- `backend/views/user_panel.py`
- `backend/views/admin.py`
- `backend/tests.py`

### Response JSON change

Response detail JSON no longer returns raw media URLs from `answer.file.url`.

It now returns:

```text
reverse("checklist_answer_download", args=[answer.id])
```

This affects:

- `user_submission_action`
- `admin_response_action`

### Security impact

Attachment access is now mediated by Django authentication and role-based response scoping instead of relying on direct media file exposure.

## Tests Added

Added tests for:

- Spoofed PDF upload rejection.
- Invalid image upload rejection.
- Oversized upload rejection.
- SVG branding upload rejection.
- Unauthorized attachment download denial.
- Authorized owner attachment download.
- Admin attachment download.

Updated existing PDF acceptance test to use a real generated PDF through `pypdf.PdfWriter`.

## Verification

### Django Check

Command:

```bash
python manage.py check
```

Result:

```text
System check identified no issues (0 silenced).
```

### Django Deploy Check

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

### Django Tests

Command:

```bash
python manage.py test
```

Result:

```text
Ran 15 tests
OK
```

Note:

- The test run emitted local Windows GLib/GIO warnings related to UWP app registrations. These warnings did not affect test success.

## Remaining Recommendations

No remaining High severity issues from the previous security review remain open.

Recommended future hardening:

- Add malware scanning for uploaded files if QCMS is deployed in an enterprise environment.
- Add login rate limiting and account lockout.
- Add Content Security Policy globally.
- Consider serving downloads with `as_attachment=True` for high-risk file categories.
- Consider removing legacy DOC/XLS support if not required by business users.
