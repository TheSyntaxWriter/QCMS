import math
from decimal import Decimal, InvalidOperation

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import RegexValidator
from .workflow_service import ResponseStatus
from .control_panel_settings import DEFAULT_SYSTEM_PREFERENCES, DEFAULT_THEME_SETTINGS


def validate_geolocation_values(latitude=None, longitude=None, accuracy=None):
    errors = {}

    for field_name, value, minimum, maximum in (
        ('latitude', latitude, Decimal('-90'), Decimal('90')),
        ('longitude', longitude, Decimal('-180'), Decimal('180')),
    ):
        if value is None:
            continue
        try:
            numeric_value = value if isinstance(value, Decimal) else Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            errors[field_name] = 'Enter a valid finite coordinate.'
            continue
        if not numeric_value.is_finite() or not minimum <= numeric_value <= maximum:
            errors[field_name] = f'Ensure this value is between {minimum} and {maximum}.'

    if accuracy is not None:
        try:
            numeric_accuracy = float(accuracy)
        except (TypeError, ValueError, OverflowError):
            errors['accuracy'] = 'Enter a valid finite accuracy.'
        else:
            if not math.isfinite(numeric_accuracy) or numeric_accuracy < 0:
                errors['accuracy'] = 'Ensure accuracy is a finite value greater than or equal to 0.'

    if errors:
        raise ValidationError(errors)


class GeolocationValidatedQuerySet(models.QuerySet):
    GEOLOCATION_FIELDS = {'latitude', 'longitude', 'accuracy'}

    @staticmethod
    def _validate_object(obj):
        validate_geolocation_values(obj.latitude, obj.longitude, obj.accuracy)

    def update(self, **kwargs):
        geolocation_values = {
            field: kwargs[field]
            for field in self.GEOLOCATION_FIELDS
            if field in kwargs
        }
        if geolocation_values:
            validate_geolocation_values(**geolocation_values)
        return super().update(**kwargs)

    def bulk_create(self, objs, **kwargs):
        for obj in objs:
            self._validate_object(obj)
        return super().bulk_create(objs, **kwargs)

    def bulk_update(self, objs, fields, **kwargs):
        if self.GEOLOCATION_FIELDS.intersection(fields):
            for obj in objs:
                self._validate_object(obj)
        return super().bulk_update(objs, fields, **kwargs)


# =========================================================
# 📁 PROJECT MASTER
# =========================================================
class Project(models.Model):

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)

    domain = models.CharField(
        max_length=50,
        choices=[
            ('Corporate', 'Corporate'),
            ('Non-Corporate', 'Non-Corporate')
        ]
    )

    is_active = models.BooleanField(default=True)

    # 🔥 Soft migration safe fields
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


# =========================================================
# 🏢 DEPARTMENT MASTER
# =========================================================
class Department(models.Model):

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)

    is_active = models.BooleanField(default=True)

    # 🔥 Soft migration safe
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


# =========================================================
# 👤 USER PROFILE
# =========================================================
class UserProfile(models.Model):

    ROLE_CHOICES = (
        ('User', 'User'),
        ('HOD', 'HOD'),
        ('Management', 'Management'),
        ('Admin', 'Admin'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    role = models.CharField(max_length=50, choices=ROLE_CHOICES)

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    assigned_hod = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_user_profiles',
        help_text='Primary HOD responsible for approving this user checklist responses.',
    )

    is_active = models.BooleanField(default=True)
    employee_id = models.CharField(max_length=64, blank=True, default='')
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        default='',
        validators=[
            RegexValidator(
                regex=r'^\+?[0-9\-\s]{7,20}$',
                message='Enter a valid phone number.'
            )
        ]
    )
    profile_image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.user.username


def checklist_answer_upload_path(instance, filename):
    """
    File naming rule:
    <checklist_id>_q<question_id>_u<user_id>_<ddmmyyyy>.<ext>
    """
    extension = filename.split('.')[-1] if '.' in filename else 'dat'
    date_str = timezone.now().strftime('%d%m%Y')
    checklist_id = (instance.response.checklist.checklist_id or f"cl{instance.response.checklist_id}").lower()
    question_id = instance.question_id or 0
    user_id = instance.response.submitted_by_id or 0
    return f"checklist_uploads/{checklist_id}_q{question_id}_u{user_id}_{date_str}.{extension}"


class ChecklistType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ChecklistDefinition(models.Model):
    checklist_id = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    checklist_type = models.ForeignKey(ChecklistType, on_delete=models.PROTECT, related_name='checklists')
    projects = models.ManyToManyField(Project, related_name='checklist_definitions', blank=True)
    departments = models.ManyToManyField(Department, related_name='checklist_definitions', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.checklist_id} - {self.name}"


class ChecklistQuestion(models.Model):
    TYPE_SHORT_TEXT = 'short_text'
    TYPE_LONG_TEXT = 'long_text'
    TYPE_MULTIPLE_CHOICE = 'multiple_choice'
    TYPE_CHECKBOX = 'checkbox'
    TYPE_DROPDOWN = 'dropdown'
    TYPE_FILE_UPLOAD = 'file_upload'
    TYPE_YES_NO = 'yes_no'
    TYPE_DATE = 'date'

    QUESTION_TYPES = (
        (TYPE_SHORT_TEXT, 'Short Text'),
        (TYPE_LONG_TEXT, 'Long Text'),
        (TYPE_MULTIPLE_CHOICE, 'Multiple Choice'),
        (TYPE_CHECKBOX, 'Checkbox'),
        (TYPE_DROPDOWN, 'Dropdown'),
        (TYPE_FILE_UPLOAD, 'File Upload'),
        (TYPE_YES_NO, 'Yes / No'),
        (TYPE_DATE, 'Date'),
    )

    checklist = models.ForeignKey(ChecklistDefinition, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    type = models.CharField(max_length=30, choices=QUESTION_TYPES)
    options = models.JSONField(default=list, blank=True)
    order = models.PositiveIntegerField(default=1)
    section = models.CharField(max_length=255, blank=True, default='')
    required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.checklist.checklist_id} - Q{self.order}"


class ChecklistResponse(models.Model):
    STATUS_CHOICES = ResponseStatus.CHOICES

    checklist = models.ForeignKey(ChecklistDefinition, on_delete=models.CASCADE, related_name='responses')
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='checklist_responses')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    hod = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='hod_reviews')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=ResponseStatus.PENDING, db_index=True)
    submitted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='response_updates')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    accuracy = models.FloatField(null=True, blank=True)
    submission_ip = models.GenericIPAddressField(null=True, blank=True)

    objects = GeolocationValidatedQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['submitted_at']),
            models.Index(fields=['project']),
            models.Index(fields=['submitted_by']),
        ]
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.checklist.checklist_id} - {self.submitted_by}"

    def clean(self):
        super().clean()
        validate_geolocation_values(self.latitude, self.longitude, self.accuracy)

    def save(self, *args, **kwargs):
        validate_geolocation_values(self.latitude, self.longitude, self.accuracy)
        return super().save(*args, **kwargs)


class ImmutableDecisionQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError('Response decisions are append-only and cannot be modified.')

    def delete(self):
        raise ValidationError('Response decisions are append-only and cannot be deleted.')


class ResponseDecisionManager(models.Manager.from_queryset(ImmutableDecisionQuerySet)):
    def bulk_create(self, objs, **kwargs):
        if kwargs.get('update_conflicts'):
            raise ValidationError('Response decisions are append-only and cannot use conflict updates.')
        for obj in objs:
            obj.full_clean()
        return super().bulk_create(objs, **kwargs)


class ResponseDecision(models.Model):
    ACTION_APPROVE = 'approve'
    ACTION_REJECT = 'reject'
    ACTION_CHOICES = (
        (ACTION_APPROVE, 'Approve'),
        (ACTION_REJECT, 'Reject'),
    )

    response = models.ForeignKey(ChecklistResponse, on_delete=models.PROTECT, related_name='decisions')
    action = models.CharField(max_length=16, choices=ACTION_CHOICES)
    comment = models.TextField(blank=True, default='')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='response_decisions')
    actor_role = models.CharField(max_length=32, blank=True, default='')
    is_override = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = ResponseDecisionManager()

    class Meta:
        ordering = ['created_at', 'id']

    def __str__(self):
        return f"{self.response_id} - {self.get_action_display()}"

    def clean(self):
        super().clean()
        if self.action == self.ACTION_REJECT and not (self.comment or '').strip():
            raise ValidationError({'comment': 'Rejection reason is required.'})

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError('Response decisions are append-only and cannot be modified.')
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Response decisions are append-only and cannot be deleted.')


class ChecklistAnswer(models.Model):
    response = models.ForeignKey(ChecklistResponse, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(ChecklistQuestion, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField(blank=True, default='')
    file = models.FileField(upload_to=checklist_answer_upload_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Checklist(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Section(models.Model):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']


class Question(models.Model):
    TYPE_SHORT_TEXT = 'short_text'
    TYPE_LONG_TEXT = 'long_text'
    TYPE_MULTIPLE_CHOICE = 'multiple_choice'
    TYPE_CHECKBOX = 'checkbox'
    TYPE_DROPDOWN = 'dropdown'
    TYPE_FILE_UPLOAD = 'file_upload'
    TYPE_YES_NO = 'yes_no'
    TYPE_DATE = 'date'

    QUESTION_TYPES = (
        (TYPE_SHORT_TEXT, 'Short Text'),
        (TYPE_LONG_TEXT, 'Long Text'),
        (TYPE_MULTIPLE_CHOICE, 'Multiple Choice'),
        (TYPE_CHECKBOX, 'Checkbox'),
        (TYPE_DROPDOWN, 'Dropdown'),
        (TYPE_FILE_UPLOAD, 'File Upload'),
        (TYPE_YES_NO, 'Yes / No'),
        (TYPE_DATE, 'Date'),
    )

    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    type = models.CharField(max_length=30, choices=QUESTION_TYPES)
    options = models.JSONField(default=list, blank=True)
    required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']


class RolePermission(models.Model):
    ROLE_CHOICES = (
        ('User', 'User'),
        ('HOD', 'HOD'),
        ('Management', 'Management'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    visible_columns = models.JSONField(default=list, blank=True)
    selected_projects = models.JSONField(default=list, blank=True)
    allowed_actions = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.role


class ImmutableActivityLogQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError('Activity logs are append-only and cannot be modified.')

    def delete(self):
        raise ValidationError('Activity logs are append-only and cannot be deleted.')

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError('Activity logs are append-only and cannot be modified.')


class ActivityLogManager(models.Manager.from_queryset(ImmutableActivityLogQuerySet)):
    def bulk_create(self, objs, **kwargs):
        if kwargs.get('update_conflicts'):
            raise ValidationError('Activity logs are append-only and cannot use conflict updates.')
        return super().bulk_create(objs, **kwargs)


class ActivityLog(models.Model):
    STATUS_SUCCESS = 'Success'
    STATUS_FAILED = 'Failed'
    STATUS_INFO = 'Info'
    STATUS_CHOICES = (
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_INFO, 'Info'),
    )
    SEVERITY_LOW = 'Low'
    SEVERITY_MEDIUM = 'Medium'
    SEVERITY_HIGH = 'High'
    SEVERITY_CRITICAL = 'Critical'
    SEVERITY_CHOICES = (
        (SEVERITY_LOW, 'Low'),
        (SEVERITY_MEDIUM, 'Medium'),
        (SEVERITY_HIGH, 'High'),
        (SEVERITY_CRITICAL, 'Critical'),
    )
    SOURCE_UI = 'UI'
    SOURCE_ADMIN = 'Admin'
    SOURCE_SYSTEM = 'System'
    SOURCE_SCRIPT = 'Script'
    SOURCE_API = 'API'
    SOURCE_CHOICES = (
        (SOURCE_UI, 'UI'),
        (SOURCE_ADMIN, 'Admin'),
        (SOURCE_SYSTEM, 'System'),
        (SOURCE_SCRIPT, 'Script'),
        (SOURCE_API, 'API'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs')
    role = models.CharField(max_length=50, blank=True, default='')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    event_key = models.CharField(max_length=160, blank=True, default='', db_index=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default=SEVERITY_MEDIUM, db_index=True)
    target_type = models.CharField(max_length=120, blank=True, default='', db_index=True)
    target_id = models.CharField(max_length=120, blank=True, default='', db_index=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_UI, db_index=True)
    action_type = models.CharField(max_length=120, db_index=True)
    module_name = models.CharField(max_length=80, db_index=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_INFO, db_index=True)
    old_data = models.JSONField(null=True, blank=True)
    new_data = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = ActivityLogManager()

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['module_name', 'action_type']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['department', 'project', 'timestamp']),
            models.Index(fields=['event_key', 'timestamp']),
            models.Index(fields=['target_type', 'target_id']),
            models.Index(fields=['severity', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M:%S} - {self.module_name} - {self.action_type}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError('Activity logs are append-only and cannot be modified.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Activity logs are append-only and cannot be deleted.')


class AppSettings(models.Model):
    web_app_name = models.CharField(max_length=120, default='QCMS')
    logo = models.ImageField(upload_to='branding/', null=True, blank=True)
    favicon = models.ImageField(upload_to='branding/', null=True, blank=True)
    sidebar_logo = models.ImageField(upload_to='branding/', null=True, blank=True)
    general_settings = models.JSONField(default=dict, blank=True)
    theme_settings = models.JSONField(default=dict, blank=True)
    system_preferences = models.JSONField(default=dict, blank=True)
    security_settings = models.JSONField(default=dict, blank=True)
    notification_settings = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                'general_settings': {'company_tagline': '', 'support_email': ''},
                'theme_settings': DEFAULT_THEME_SETTINGS.copy(),
                'system_preferences': DEFAULT_SYSTEM_PREFERENCES.copy(),
                'security_settings': {
                    'session_timeout': 30,
                    'password_rotation_days': 90,
                    'geolocation_tracking_enabled': False,
                },
                'notification_settings': {'email_alerts': True, 'in_app_alerts': True},
            },
        )
        return obj


class NotificationSetting(models.Model):
    enable_notifications = models.BooleanField(default=True)
    enable_bell = models.BooleanField(default=True)
    enable_popups = models.BooleanField(default=True)
    enable_sound = models.BooleanField(default=False)
    retention_days = models.PositiveIntegerField(default=365)
    low_color = models.CharField(max_length=7, default='#6B7280')
    medium_color = models.CharField(max_length=7, default='#2563EB')
    high_color = models.CharField(max_length=7, default='#EA580C')
    critical_color = models.CharField(max_length=7, default='#DC2626')
    event_settings = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notification_setting_updates',
    )

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'Notification Settings'


class Notification(models.Model):
    PRIORITY_LOW = 'Low'
    PRIORITY_MEDIUM = 'Medium'
    PRIORITY_HIGH = 'High'
    PRIORITY_CRITICAL = 'Critical'
    PRIORITY_CHOICES = (
        (PRIORITY_LOW, PRIORITY_LOW),
        (PRIORITY_MEDIUM, PRIORITY_MEDIUM),
        (PRIORITY_HIGH, PRIORITY_HIGH),
        (PRIORITY_CRITICAL, PRIORITY_CRITICAL),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    event_key = models.CharField(max_length=80, db_index=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(max_length=16, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM, db_index=True)
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    action_required = models.BooleanField(default=False, db_index=True)
    related_type = models.CharField(max_length=80, blank=True, default='')
    related_id = models.CharField(max_length=64, blank=True, default='')
    related_url = models.CharField(max_length=500, blank=True, default='')
    popup_shown_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['recipient', 'is_read', 'created_at']),
            models.Index(fields=['recipient', 'action_required', 'created_at']),
        ]

    def __str__(self):
        return f'{self.recipient} - {self.title}'
