# Activity Log Phase 0 Fix Report

## Summary

Fixed the remaining append-only bypass identified in the Activity Log Phase 0 review. `ActivityLog.objects.bulk_create(update_conflicts=True)` now raises `ValidationError` before any database write can occur.

## Files Changed

- `backend/models.py`
- `backend/tests.py`

## Fix Implemented

### Conflict-Update Bulk Create Blocked

`ActivityLogManager.bulk_create()` now rejects conflict-update mode:

- `bulk_create(update_conflicts=True)` raises `ValidationError`.
- Existing rows cannot be overwritten through conflict updates.
- Normal `bulk_create()` for inserting new log rows remains supported.

## Tests Added

Added regression coverage for:

- Normal `ActivityLog.objects.bulk_create()` inserts new records successfully.
- `ActivityLog.objects.bulk_create(update_conflicts=True)` fails with `ValidationError`.
- Existing rows remain unchanged after a rejected conflict-update attempt.

## Verification

Executed:

```text
python manage.py check
python manage.py test
```

Results:

```text
System check identified no issues (0 silenced).
Ran 77 tests in 172.643s
OK
```

## Migration Notes

No migration was required for this fix because the change is manager-level behavior only.

`python manage.py makemigrations --check --dry-run` still reports an unrelated pre-existing `AppSettings.web_app_name` model/migration drift. No migration was created because it is outside the Activity Log Phase 0 bypass fix scope.

## Self-Review

- Normal log creation still works.
- Normal bulk creation still works.
- Instance update/delete remains blocked.
- Queryset update/delete remains blocked.
- Bulk update remains blocked.
- Conflict-update bulk create is now blocked.
- Existing ActivityLog rows remain unchanged after rejected overwrite attempts.
- No schema or application workflow changes were introduced.

READY FOR ACTIVITY LOG PHASE 0 MERGE
