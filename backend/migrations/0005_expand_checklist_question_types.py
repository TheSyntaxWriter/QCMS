# Generated manually on 2026-05-06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0004_rolepermission_selected_projects'),
    ]

    operations = [
        migrations.AlterField(
            model_name='checklistquestion',
            name='type',
            field=models.CharField(
                choices=[
                    ('short_text', 'Short Text'),
                    ('long_text', 'Long Text'),
                    ('multiple_choice', 'Multiple Choice'),
                    ('checkbox', 'Checkbox'),
                    ('dropdown', 'Dropdown'),
                    ('file_upload', 'File Upload'),
                    ('yes_no', 'Yes / No'),
                    ('date', 'Date'),
                ],
                max_length=30,
            ),
        ),
    ]
