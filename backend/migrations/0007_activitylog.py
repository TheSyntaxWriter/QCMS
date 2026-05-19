from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0006_merge_20260506_1141'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(blank=True, default='', max_length=50)),
                ('action_type', models.CharField(db_index=True, max_length=120)),
                ('module_name', models.CharField(db_index=True, max_length=80)),
                ('description', models.TextField()),
                ('ip_address', models.GenericIPAddressField(blank=True, db_index=True, null=True)),
                ('user_agent', models.TextField(blank=True, default='')),
                ('status', models.CharField(choices=[('Success', 'Success'), ('Failed', 'Failed'), ('Info', 'Info')], db_index=True, default='Info', max_length=20)),
                ('old_data', models.JSONField(blank=True, null=True)),
                ('new_data', models.JSONField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='backend.department')),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='backend.project')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='activity_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp'],
                'indexes': [models.Index(fields=['module_name', 'action_type'], name='backend_act_module__d1a7fa_idx'), models.Index(fields=['user', 'timestamp'], name='backend_act_user_id_2ab793_idx'), models.Index(fields=['department', 'project', 'timestamp'], name='backend_act_departm_239609_idx')],
            },
        ),
    ]
