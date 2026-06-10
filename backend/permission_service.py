from django.db.models import Q

from .models import ChecklistResponse, RolePermission
from .workflow_service import can_edit_response, can_approve_response, can_reject_response, evaluate_status_action

VALID_COLUMNS = [
    'checklist_id', 'checklist_name', 'checklist_type', 'submitted_by',
    'project', 'department', 'hod_name', 'submission_datetime', 'status',
    'last_updated_by', 'last_updated', 'actions',
]
VALID_ACTIONS = ['view', 'edit', 'approve', 'reject', 'delete', 'toggle']

ROLE_SCOPED_ACTIONS = {
    'Admin': set(VALID_ACTIONS),
    'Management': {'view', 'approve', 'reject'},
    'HOD': {'view', 'approve', 'reject'},
    'User': {'view', 'edit'},
}


def normalize_values(items, allowed_values):
    if not isinstance(items, list):
        return []
    normalized = []
    for item in items:
        value = (item or '').strip() if isinstance(item, str) else ''
        if value in allowed_values and value not in normalized:
            normalized.append(value)
    return normalized


def get_role_permission_config(role):
    if role == 'Admin':
        return VALID_COLUMNS, VALID_ACTIONS
    permission = RolePermission.objects.filter(role=role).first()
    if not permission:
        return VALID_COLUMNS, []

    columns = normalize_values(permission.visible_columns or VALID_COLUMNS, VALID_COLUMNS)
    actions = normalize_values(permission.allowed_actions or [], VALID_ACTIONS)
    scoped_actions = ROLE_SCOPED_ACTIONS.get(role, set())
    actions = [a for a in actions if a in scoped_actions]
    return columns, actions


def responses_for_profile(profile, user):
    qs = ChecklistResponse.objects.select_related(
        'checklist', 'submitted_by', 'project', 'department', 'hod', 'updated_by', 'checklist__checklist_type',
    )
    if profile.role == 'Admin':
        return qs
    if profile.role == 'User':
        return qs.filter(submitted_by=user)
    if profile.role == 'HOD':
        query = Q(department=profile.department)
        if profile.project:
            query &= Q(project=profile.project)
        if profile.project and profile.project.domain:
            query &= Q(project__domain=profile.project.domain)
        return qs.filter(query)
    if profile.role == 'Management':
        query = Q()
        if profile.department:
            query &= Q(department=profile.department)
        if profile.project:
            query &= Q(project=profile.project)
            query &= Q(project__domain=profile.project.domain)
        return qs.filter(query) if query else qs.none()
    return qs.none()


def validate_permission_payload(columns, actions):
    normalized_columns = normalize_values(columns, VALID_COLUMNS)
    normalized_actions = normalize_values(actions, VALID_ACTIONS)
    if not normalized_columns:
        raise ValueError('At least one visible column is required.')
    invalid_actions = [a for a in actions if a not in VALID_ACTIONS]
    if invalid_actions:
        raise ValueError(f'Invalid actions: {", ".join(invalid_actions)}')
    return normalized_columns, normalized_actions


def is_action_permitted_for_response(action, response, profile, user):
    """
    Backend-safe policy layer that evaluates workflow allowance in addition to
    role-level action visibility from RolePermission.
    """
    if action == 'view':
        return True
    if action == 'delete':
        return profile.role == 'Admin'
    if action == 'toggle':
        return profile.role == 'Admin' and evaluate_status_action(response.status, 'toggle').allowed
    if action == 'edit':
        return can_edit_response(response, user, profile.role)
    if action == 'approve':
        return can_approve_response(response, profile.role)
    if action == 'reject':
        return can_reject_response(response, profile.role)
    return False


def effective_allowed_actions_for_response(base_actions, response, profile, user):
    return [action for action in base_actions if is_action_permitted_for_response(action, response, profile, user)]
