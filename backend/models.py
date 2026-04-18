from django.db import models
from django.contrib.auth.models import User


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