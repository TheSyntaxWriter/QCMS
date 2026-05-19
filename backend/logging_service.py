from contextvars import ContextVar
from typing import Any

from .models import ActivityLog, UserProfile

_current_request: ContextVar = ContextVar('current_request', default=None)


def set_current_request(request):
    _current_request.set(request)


def get_current_request():
    return _current_request.get()


def get_request_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def write_activity_log(*, action_type: str, module_name: str, description: str, status: str = ActivityLog.STATUS_INFO,
                       user=None, old_data: dict[str, Any] | None = None, new_data: dict[str, Any] | None = None):
    request = get_current_request()
    profile = None

    if user and getattr(user, 'is_authenticated', False):
        profile = UserProfile.objects.filter(user=user).select_related('department', 'project').first()

    ActivityLog.objects.create(
        user=user if getattr(user, 'is_authenticated', False) else None,
        role=profile.role if profile else '',
        department=profile.department if profile else None,
        project=profile.project if profile else None,
        action_type=action_type,
        module_name=module_name,
        description=description,
        ip_address=get_request_ip(request) if request else None,
        user_agent=(request.META.get('HTTP_USER_AGENT', '') if request else ''),
        status=status,
        old_data=old_data,
        new_data=new_data,
    )
