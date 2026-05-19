from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0007_activitylog'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='employee_id',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='phone_number',
            field=models.CharField(blank=True, default='', max_length=20, validators=[django.core.validators.RegexValidator(message='Enter a valid phone number.', regex='^\\+?[0-9\\-\\s]{7,20}$')]),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='profile_image',
            field=models.ImageField(blank=True, null=True, upload_to='profile_images/'),
        ),
    ]
