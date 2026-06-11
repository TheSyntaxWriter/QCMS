from datetime import timedelta

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from .models import ActivityLog, Notification, NotificationSetting, UserProfile


EVENT_DEFINITIONS = {
    'checklist_submitted': ('Checklist Submitted Successfully', Notification.PRIORITY_MEDIUM, False),
    'checklist_approved': ('Checklist Approved', Notification.PRIORITY_MEDIUM, False),
    'checklist_rejected': ('Checklist Rejected', Notification.PRIORITY_HIGH, True),
    'rejection_comment_available': ('Rejection Comment Available', Notification.PRIORITY_HIGH, True),
    'checklist_resubmitted': ('Checklist Resubmitted', Notification.PRIORITY_MEDIUM, False),
    'new_approval_request': ('New Approval Request', Notification.PRIORITY_HIGH, True),
    'rejected_response_resubmitted': ('Rejected Response Resubmitted', Notification.PRIORITY_HIGH, True),
    'user_assigned_to_hod': ('User Assigned To HOD', Notification.PRIORITY_MEDIUM, False),
    'user_removed_from_hod': ('User Removed From HOD', Notification.PRIORITY_MEDIUM, False),
    'missing_assigned_hod_alert': ('Missing Assigned HOD Alert', Notification.PRIORITY_HIGH, True),
    'override_approval_performed': ('Override Approval Performed', Notification.PRIORITY_HIGH, True),
    'override_rejection_performed': ('Override Rejection Performed', Notification.PRIORITY_HIGH, True),
    'user_created': ('User Created', Notification.PRIORITY_LOW, False),
    'user_deactivated': ('User Deactivated', Notification.PRIORITY_HIGH, True),
    'notification_settings_changed': ('Notification Settings Changed', Notification.PRIORITY_HIGH, True),
    'missing_hod_assignment_detected': ('Missing HOD Assignment Detected', Notification.PRIORITY_CRITICAL, True),
    'suspicious_upload_rejected': ('Suspicious Upload Rejected', Notification.PRIORITY_HIGH, True),
    'permission_denied_threshold': ('Permission Denied Threshold Reached', Notification.PRIORITY_CRITICAL, True),
    'geolocation_capture_failed': ('Geolocation Capture Failed', Notification.PRIORITY_LOW, False),
    'protected_audit_action_blocked': ('Protected Audit Action Blocked', Notification.PRIORITY_CRITICAL, True),
}


def effective_event_settings(settings=None):
    settings = settings or NotificationSetting.get_solo()
    configured = settings.event_settings or {}
    return {
        key: {
            'name': name,
            'enabled': configured.get(key, {}).get('enabled', True),
            'priority': configured.get(key, {}).get('priority', priority),
            'popup': configured.get(key, {}).get('popup', popup),
        }
        for key, (name, priority, popup) in EVENT_DEFINITIONS.items()
    }


def users_for_role(role):
    return User.objects.filter(
        userprofile__role=role,
        userprofile__is_active=True,
        is_active=True,
    ).distinct()


def create_notifications(event_key, recipients, *, title=None, message, related_type='', related_id='', related_url='', action_required=False):
    settings = NotificationSetting.get_solo()
    event = effective_event_settings(settings).get(event_key)
    if not settings.enable_notifications or not event or not event['enabled']:
        return []

    if isinstance(recipients, User):
        recipients = [recipients]
    recipient_ids = []
    for recipient in recipients:
        recipient_id = recipient.pk if isinstance(recipient, User) else int(recipient)
        if recipient_id not in recipient_ids:
            recipient_ids.append(recipient_id)

    active_ids = set(User.objects.filter(id__in=recipient_ids, is_active=True).values_list('id', flat=True))
    rows = [
        Notification(
            recipient_id=recipient_id,
            event_key=event_key,
            title=title or event['name'],
            message=message,
            priority=event['priority'],
            action_required=action_required,
            related_type=related_type,
            related_id=str(related_id or ''),
            related_url=related_url,
        )
        for recipient_id in recipient_ids
        if recipient_id in active_ids
    ]
    return Notification.objects.bulk_create(rows)


def notify_on_commit(event_key, recipients, **kwargs):
    recipient_ids = [recipients.pk] if isinstance(recipients, User) else [item.pk if isinstance(item, User) else int(item) for item in recipients]
    transaction.on_commit(lambda: create_notifications(event_key, recipient_ids, **kwargs))


def purge_expired_notifications():
    days = max(NotificationSetting.get_solo().retention_days, 1)
    return Notification.objects.filter(created_at__lt=timezone.now() - timedelta(days=days)).delete()


def assigned_hod_is_valid(profile):
    hod = getattr(profile, 'assigned_hod', None)
    if not hod or not hod.is_active:
        return False
    hod_profile = UserProfile.objects.filter(user=hod, role='HOD', is_active=True).first()
    return bool(hod_profile)


def record_permission_denied(user, description):
    now = timezone.now()
    ActivityLog.objects.create(
        user=user,
        role=getattr(getattr(user, 'userprofile', None), 'role', ''),
        action_type='Permission Denied',
        module_name='Security',
        description=description,
        status=ActivityLog.STATUS_FAILED,
    )
    window_start = now - timedelta(minutes=15)
    denied_count = ActivityLog.objects.filter(
        user=user,
        action_type='Permission Denied',
        timestamp__gte=window_start,
    ).count()
    already_alerted = Notification.objects.filter(
        event_key='permission_denied_threshold',
        related_type='User',
        related_id=str(user.id),
        created_at__gte=window_start,
    ).exists()
    if denied_count >= 5 and not already_alerted:
        create_notifications(
            'permission_denied_threshold',
            users_for_role('Admin'),
            message=f'{user.username} reached {denied_count} denied actions within 15 minutes.',
            related_type='User',
            related_id=user.id,
            related_url='/admin-panel/logs/',
            action_required=True,
        )
