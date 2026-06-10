# Project Structure and Admin Users Tab Review

Date: 2026-04-21

## High-priority suggestions

1. **Use POST (with CSRF) for destructive user actions.**
   - The `delete` and `toggle` operations are currently triggered via query parameters in GET URLs.
   - Suggestion: replace these links with `<form method="post">` submit buttons and validate CSRF token server-side.

2. **Add server-side validation and permission checks for user create/edit.**
   - Validate unique usernames and role/department/project combinations.
   - Return user-friendly error messages instead of relying on model/database exceptions.

3. **Add pagination to admin users list.**
   - Current page loads all users at once and computes multiple filtered aggregates.
   - Suggestion: use Django paginator (`?page=`) and consider moving chart data queries to lightweight aggregated endpoints.

## Medium-priority suggestions

4. **Remove duplication and split responsibilities in Users frontend code.**
   - There is a fully inlined JS implementation in `admin_users.html` while a separate `frontend/static/admin_users/admin_users.js` file also exists.
   - Suggestion: keep one implementation only, and load JS from static files.

5. **Reduce inline styling in templates.**
   - `admin_users.html` has many inline `style="..."` blocks that make maintenance harder.
   - Suggestion: shift these to `admin_users.css` classes.

6. **Standardize naming and route aliases.**
   - Routes include both `admin-create/` and `admin-master-create/` pointing to similar create behavior.
   - Suggestion: keep one canonical route and deprecate aliases.

7. **Improve query design for chart data under filters.**
   - Role counts are based on filtered `user_list`, while department chart data is computed globally from `Department.objects.annotate(...)`.
   - Suggestion: choose a consistent behavior (global vs filtered) and label charts accordingly.

## Nice-to-have suggestions

8. **Accessibility and semantics improvements.**
   - Convert clickable action links wrapping buttons into proper buttons/forms.
   - Add ARIA labels for icon-only controls (search icon button, close modal, etc.).

9. **Refactor repeated auth/role gating into decorators.**
   - Multiple admin views duplicate "authenticated + Admin role" checks.
   - Suggestion: create reusable decorators/mixins for consistency.

10. **Prepare for larger codebase growth by modularizing app layers.**
    - Consider separating `services/` for business logic and `selectors/` for complex query composition.
    - Keep views focused on orchestration and HTTP handling.
