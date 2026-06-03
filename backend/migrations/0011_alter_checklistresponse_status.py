from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0010_appsettings'),
    ]

    operations = [
        migrations.AlterField(
            model_name='checklistresponse',
            name='status',
            field=models.CharField(
                choices=[
                    ('WIP', 'WIP'),
                    ('Pending for Approval', 'Pending for Approval'),
                    ('Pending', 'Pending'),
                    ('Approved', 'Approved'),
                    ('Rejected', 'Rejected'),
                ],
                db_index=True,
                default='Pending',
                max_length=32,
            ),
        ),
    ]
