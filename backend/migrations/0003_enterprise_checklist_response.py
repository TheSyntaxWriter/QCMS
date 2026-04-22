# Generated manually on 2026-04-22

import backend.models
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def seed_checklist_types(apps, schema_editor):
    checklist_type_model = apps.get_model('backend', 'ChecklistType')
    for name in ['Daily', 'Weekly', 'Monthly', 'Activity']:
        checklist_type_model.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0002_answer_created_at_checklist_created_at_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChecklistType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='ChecklistDefinition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('checklist_id', models.CharField(db_index=True, max_length=20, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('checklist_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='checklists', to='backend.checklisttype')),
                ('departments', models.ManyToManyField(blank=True, related_name='checklist_definitions', to='backend.department')),
                ('projects', models.ManyToManyField(blank=True, related_name='checklist_definitions', to='backend.project')),
            ],
            options={'ordering': ['-updated_at']},
        ),
        migrations.CreateModel(
            name='RolePermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('User', 'User'), ('HOD', 'HOD'), ('Management', 'Management')], max_length=20, unique=True)),
                ('visible_columns', models.JSONField(blank=True, default=list)),
                ('allowed_actions', models.JSONField(blank=True, default=list)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='ChecklistQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_text', models.TextField()),
                ('type', models.CharField(choices=[('short_text', 'Short Text'), ('long_text', 'Long Text'), ('dropdown', 'Dropdown'), ('multiple_choice', 'Multiple Choice'), ('file_upload', 'File Upload')], max_length=30)),
                ('options', models.JSONField(blank=True, default=list)),
                ('order', models.PositiveIntegerField(default=1)),
                ('section', models.CharField(blank=True, default='', max_length=255)),
                ('required', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('checklist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='backend.checklistdefinition')),
            ],
            options={'ordering': ['order', 'id']},
        ),
        migrations.CreateModel(
            name='ChecklistResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')], db_index=True, default='Pending', max_length=20)),
                ('submitted_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('checklist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='backend.checklistdefinition')),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='backend.department')),
                ('hod', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='hod_reviews', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='backend.project')),
                ('submitted_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='checklist_responses', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='response_updates', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-submitted_at']},
        ),
        migrations.CreateModel(
            name='ChecklistAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer_text', models.TextField(blank=True, default='')),
                ('file', models.FileField(blank=True, null=True, upload_to=backend.models.checklist_answer_upload_path)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='backend.checklistquestion')),
                ('response', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='backend.checklistresponse')),
            ],
        ),
        migrations.AddIndex(
            model_name='checklistresponse',
            index=models.Index(fields=['status'], name='backend_che_status_42a098_idx'),
        ),
        migrations.AddIndex(
            model_name='checklistresponse',
            index=models.Index(fields=['submitted_at'], name='backend_che_submitt_e7ce4d_idx'),
        ),
        migrations.AddIndex(
            model_name='checklistresponse',
            index=models.Index(fields=['project'], name='backend_che_project_db0d4c_idx'),
        ),
        migrations.AddIndex(
            model_name='checklistresponse',
            index=models.Index(fields=['submitted_by'], name='backend_che_submitt_92ec81_idx'),
        ),
        migrations.RunPython(code=seed_checklist_types, reverse_code=migrations.RunPython.noop),
    ]
