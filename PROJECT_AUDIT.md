# Project Audit (2026-05-04)

## Pending / not-working modules (found by static review)

1. **Checklist submission/detail flow is not wired in URLconf**
   - Templates call URL names `checklist_detail` and `view_checklist`, but these routes are not defined in `backend/urls.py`.
   - Impact: pages that render these links will fail at template-render time with `NoReverseMatch`.

2. **HOD workflow is partially implemented but not wired in URLconf**
   - HOD template links to `hod_dashboard` and `update_status`, but those routes are not defined in `backend/urls.py`.
   - Impact: HOD dashboard/actions are not reachable.

3. **Management dashboard module exists but is unreachable**
   - `management_dashboard` view exists but has no matching URL route.
   - Impact: Management role has no direct navigation endpoint.

## Count summary
- Pending/not-working modules: **3**

## High-value improvements

- Add missing URL routes for checklist/HOD/management modules and include them in navigation.
- Add Django tests for URL reverse + view status by role (Admin/User/HOD/Management) to catch broken routing quickly.
- Standardize action endpoints to POST+CSRF only for destructive/toggle actions.
- Consolidate frontend JS/CSS (remove duplicated inline JS in admin templates; keep static assets canonical).
- Add CI checks (`python manage.py check`, tests, lint) inside a reproducible virtualenv/requirements lock.

## Environment limitation found during audit
- Local validation command `python manage.py check` could not run because Django is not installed in this runtime environment.
