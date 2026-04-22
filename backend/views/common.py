from django.shortcuts import redirect

from ..models import Checklist, ChecklistDefinition, ChecklistType, UserProfile


def get_user_profile(user):
    if not user or not user.is_authenticated:
        return None
    return UserProfile.objects.filter(user=user).first()


def redirect_for_profile(profile):
    if not profile:
        return redirect('login')

    if profile.role in {'User', 'HOD'}:
        return redirect('my_checklists')
    if profile.role == 'Management':
        return redirect('dashboard')
    if profile.role == 'Admin':
        return redirect('admin_dashboard')
    return redirect('login')


def ensure_legacy_checklists_synced():
    """
    Backfill legacy Checklist rows into ChecklistDefinition so both admin and user panel
    read from one source of truth (ChecklistDefinition).
    """
    legacy_rows = Checklist.objects.select_related('project', 'department').all()
    if not legacy_rows.exists():
        return

    checklist_type_cache = {
        item.name.lower(): item
        for item in ChecklistType.objects.all()
    }

    for legacy in legacy_rows:
        type_name = (legacy.checklist_type or 'Daily').strip() or 'Daily'
        type_key = type_name.lower()
        checklist_type = checklist_type_cache.get(type_key)
        if not checklist_type:
            checklist_type = ChecklistType.objects.create(name=type_name, is_active=True)
            checklist_type_cache[type_key] = checklist_type

        definition, _ = ChecklistDefinition.objects.get_or_create(
            checklist_id=legacy.code,
            defaults={
                'name': legacy.name,
                'checklist_type': checklist_type,
                'is_active': legacy.is_active,
            },
        )

        changed = False
        if definition.name != legacy.name:
            definition.name = legacy.name
            changed = True
        if definition.checklist_type_id != checklist_type.id:
            definition.checklist_type = checklist_type
            changed = True
        if definition.is_active != legacy.is_active:
            definition.is_active = legacy.is_active
            changed = True
        if changed:
            definition.save(update_fields=['name', 'checklist_type', 'is_active', 'updated_at'])

        if legacy.project:
            definition.projects.add(legacy.project)
        if legacy.department:
            definition.departments.add(legacy.department)
