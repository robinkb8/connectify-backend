# Generated by Django 5.2.3 on 2025-07-09 06:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_emailotp'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_pro',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='pro_upgraded_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
