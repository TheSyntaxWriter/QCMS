from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0003_enterprise_checklist_response'),
    ]

    operations = [
        migrations.AddField(
            model_name='rolepermission',
            name='selected_projects',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
