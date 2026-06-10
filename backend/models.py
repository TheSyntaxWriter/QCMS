from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import RegexValidator
from .workflow_service import ResponseStatus


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


class ActivityLog(models.Model):
    STATUS_SUCCESS = 'Success'
    STATUS_FAILED = 'Failed'
    STATUS_INFO = 'Info'
    STATUS_CHOICES = (
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_INFO, 'Info'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs')
    role = models.CharField(max_length=50, blank=True, default='')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=120, db_index=True)
    module_name = models.CharField(max_length=80, db_index=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_INFO, db_index=True)
    old_data = models.JSONField(null=True, blank=True)
    new_data = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['module_name', 'action_type']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['department', 'project', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M:%S} - {self.module_name} - {self.action_type}"


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
                'theme_settings': {
                    'mode': 'light',
                    'primary_color': '#4f46e5',
                    'sidebar_color': '#0b1b68',
                    'header_color': '#0b1b68',
                    'button_style': 'rounded',
                    'font_family': 'Poppins',
                    'layout_width': 'boxed',
                },
                'system_preferences': {'timezone': 'UTC', 'date_format': 'YYYY-MM-DD'},
                'security_settings': {'session_timeout': 30, 'password_rotation_days': 90},
                'notification_settings': {'email_alerts': True, 'in_app_alerts': True},
            },
        )
        return obj
