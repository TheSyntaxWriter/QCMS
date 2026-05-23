from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0009_section_remove_answer_question_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('web_app_name', models.CharField(default='QCMS - Quality Control Management System', max_length=120)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='branding/')),
                ('favicon', models.ImageField(blank=True, null=True, upload_to='branding/')),
                ('sidebar_logo', models.ImageField(blank=True, null=True, upload_to='branding/')),
                ('general_settings', models.JSONField(blank=True, default=dict)),
                ('theme_settings', models.JSONField(blank=True, default=dict)),
                ('system_preferences', models.JSONField(blank=True, default=dict)),
                ('security_settings', models.JSONField(blank=True, default=dict)),
                ('notification_settings', models.JSONField(blank=True, default=dict)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
