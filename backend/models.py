from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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

    is_active = models.BooleanField(default=True)

    # 🔥 Soft migration safe
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.user.username


# =========================================================
# 📋 CHECKLIST MASTER
# =========================================================
class Checklist(models.Model):

    CHECKLIST_TYPE = (
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
        ('Activity', 'Activity'),
    )

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)

    checklist_type = models.CharField(
        max_length=50,
        choices=CHECKLIST_TYPE,
        default='Daily'
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    # 🔥 Soft migration safe
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


# =========================================================
# ❓ QUESTION MASTER
# =========================================================
class Question(models.Model):

    QUESTION_TYPE = (
        ('Yes/No', 'Yes/No'),
        ('Text', 'Text'),
        ('Date', 'Date'),
        ('File', 'File'),
    )

    code = models.CharField(max_length=50, unique=True)

    checklist = models.ForeignKey(
        Checklist,
        on_delete=models.CASCADE,
        related_name='questions'
    )

    question_text = models.TextField()

    question_type = models.CharField(
        max_length=50,
        choices=QUESTION_TYPE
    )

    is_mandatory = models.BooleanField(default=False)

    # 🔥 Soft migration safe
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.question_text


# =========================================================
# 🔥 CHECKLIST TRANSACTION
# =========================================================
class ChecklistTransaction(models.Model):

    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )

    transaction_id = models.CharField(max_length=100, unique=True)

    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')

    remarks = models.TextField(null=True, blank=True)

    submitted_date = models.DateTimeField(auto_now_add=True)

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_by_user'
    )

    approval_date = models.DateTimeField(null=True, blank=True)

    last_updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_by_user'
    )

    last_updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.transaction_id} - {self.checklist.name}"


# =========================================================
# 📝 ANSWER TABLE
# =========================================================
class Answer(models.Model):

    transaction = models.ForeignKey(
        ChecklistTransaction,
        on_delete=models.CASCADE,
        related_name='answers'
    )

    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    answer = models.TextField()

    # 🔥 Soft migration safe
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.question.question_text} - {self.answer}"


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
    QUESTION_TYPES = (
        ('short_text', 'Short Text'),
        ('long_text', 'Long Text'),
        ('dropdown', 'Dropdown'),
        ('multiple_choice', 'Multiple Choice'),
        ('file_upload', 'File Upload'),
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
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )

    checklist = models.ForeignKey(ChecklistDefinition, on_delete=models.CASCADE, related_name='responses')
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='checklist_responses')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    hod = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='hod_reviews')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', db_index=True)
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
