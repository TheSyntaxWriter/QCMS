import re

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from ..logging_service import write_activity_log
from ..models import ActivityLog, Notification, NotificationSetting
from ..notification_service import EVENT_DEFINITIONS, create_notifications, effective_event_settings, purge_expired_notifications, users_for_role
from .admin import _admin_sidebar_menu
from .common import get_user_profile


HEX_COLOR = re.compile(r'^#[0-9A-Fa-f]{6}$')


def _authenticated_json(request):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Authentication required'}, status=401)
    return None


def _serialize(notification):
    return {
        'id': notification.id,
        'event_key': notification.event_key,
        'title': notification.title,
        'message': notification.message,
        'priority': notification.priority,
        'is_read': notification.is_read,
        'action_required': notification.action_required,
        'related_url': notification.related_url,
        'created_at': notification.created_at.isoformat(),
    }


@require_GET
def notification_list(request):
    denied = _authenticated_json(request)
    if denied:
        return denied
    tab = request.GET.get('tab', 'all')
    queryset = Notification.objects.filter(recipient=request.user)
    if tab == 'unread':
        queryset = queryset.filter(is_read=False)
    elif tab == 'action':
        queryset = queryset.filter(action_required=True)
    return JsonResponse({'ok': True, 'notifications': [_serialize(item) for item in queryset[:50]]})


@require_GET
def notification_poll(request):
    denied = _authenticated_json(request)
    if denied:
        return denied
    settings = NotificationSetting.get_solo()
    if not settings.enable_notifications:
        return JsonResponse({'ok': True, 'unread_count': 0, 'popups': [], 'bell_enabled': False})

    purge_expired_notifications()
    queryset = Notification.objects.filter(recipient=request.user)
    unread_count = queryset.filter(is_read=False).count()
    popups = []
    if settings.enable_popups:
        event_settings = effective_event_settings(settings)
        popup_keys = [key for key, value in event_settings.items() if value['enabled'] and value['popup']]
        candidates = list(queryset.filter(
            is_read=False,
            popup_shown_at__isnull=True,
            event_key__in=popup_keys,
            priority__in=[Notification.PRIORITY_HIGH, Notification.PRIORITY_CRITICAL],
        ).order_by('created_at')[:3])
        popups = [_serialize(item) for item in candidates]
        if candidates:
            Notification.objects.filter(id__in=[item.id for item in candidates]).update(popup_shown_at=timezone.now())

    return JsonResponse({
        'ok': True,
        'unread_count': unread_count,
        'popups': popups,
        'bell_enabled': settings.enable_bell,
        'sound_enabled': settings.enable_sound,
        'colors': {
            'Low': settings.low_color,
            'Medium': settings.medium_color,
            'High': settings.high_color,
            'Critical': settings.critical_color,
        },
    })


@require_POST
def notification_mark_read(request, notification_id):
    denied = _authenticated_json(request)
    if denied:
        return denied
    updated = Notification.objects.filter(id=notification_id, recipient=request.user).update(
        is_read=True,
        read_at=timezone.now(),
    )
    return JsonResponse({'ok': bool(updated)}, status=200 if updated else 404)


@require_POST
def notification_mark_all_read(request):
    denied = _authenticated_json(request)
    if denied:
        return denied
    updated = Notification.objects.filter(recipient=request.user, is_read=False).update(
        is_read=True,
        read_at=timezone.now(),
    )
    return JsonResponse({'ok': True, 'updated': updated})


@require_POST
def notification_delete(request, notification_id):
    denied = _authenticated_json(request)
    if denied:
        return denied
    deleted, _ = Notification.objects.filter(id=notification_id, recipient=request.user).delete()
    return JsonResponse({'ok': bool(deleted)}, status=200 if deleted else 404)


def admin_notification_settings(request):
    if not request.user.is_authenticated:
        return redirect('login')
    profile = get_user_profile(request.user)
    if not profile or profile.role != 'Admin':
        return redirect('home')

    settings = NotificationSetting.get_solo()
    if request.method == 'POST':
        retention_raw = request.POST.get('retention_days', '365')
        try:
            retention_days = min(max(int(retention_raw), 1), 3650)
        except ValueError:
            retention_days = 365

        colors = {}
        for field in ('low_color', 'medium_color', 'high_color', 'critical_color'):
            value = request.POST.get(field, '').strip()
            colors[field] = value if HEX_COLOR.match(value) else getattr(settings, field)

        event_settings = {}
        valid_priorities = {choice[0] for choice in Notification.PRIORITY_CHOICES}
        for key, (_, default_priority, default_popup) in EVENT_DEFINITIONS.items():
            priority = request.POST.get(f'event_{key}_priority', default_priority)
            event_settings[key] = {
                'enabled': request.POST.get(f'event_{key}_enabled') == 'on',
                'priority': priority if priority in valid_priorities else default_priority,
                'popup': request.POST.get(f'event_{key}_popup') == 'on',
            }

        settings.enable_notifications = request.POST.get('enable_notifications') == 'on'
        settings.enable_bell = request.POST.get('enable_bell') == 'on'
        settings.enable_popups = request.POST.get('enable_popups') == 'on'
        settings.enable_sound = request.POST.get('enable_sound') == 'on'
        settings.retention_days = retention_days
        settings.event_settings = event_settings
        settings.updated_by = request.user
        for field, value in colors.items():
            setattr(settings, field, value)
        settings.save()

        create_notifications(
            'notification_settings_changed',
            users_for_role('Admin'),
            message=f'Notification Center settings were updated by {request.user.username}.',
            related_type='NotificationSetting',
            related_id=settings.pk,
            related_url=request.path,
        )
        write_activity_log(
            action_type='Notification Settings Changed',
            module_name='Notifications',
            description=f'Notification settings updated by {request.user.username}.',
            status=ActivityLog.STATUS_SUCCESS,
            user=request.user,
        )
        messages.success(request, 'Notification settings saved.')
        return redirect('admin_notification_settings')

    return render(request, 'admin_panel/admin_notification_settings.html', {
        'settings': settings,
        'event_settings': effective_event_settings(settings),
        'priority_choices': Notification.PRIORITY_CHOICES,
        'sidebar_menu': _admin_sidebar_menu(),
    })
