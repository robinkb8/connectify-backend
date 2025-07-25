# Generated by Django 5.2.1 on 2025-06-16 11:26

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(help_text="User's email address - used for login", max_length=254, unique=True)),
                ('username', models.CharField(help_text='Unique username for the user', max_length=30, unique=True, validators=[django.core.validators.RegexValidator(message='Username can only contain letters, numbers, dots, and underscores', regex='^[a-zA-Z0-9._]*$')])),
                ('full_name', models.CharField(help_text="User's full name", max_length=50)),
                ('phone', models.CharField(help_text='10-digit Indian mobile number', max_length=10, unique=True, validators=[django.core.validators.RegexValidator(message='Phone number must be 10 digits starting with 6, 7, 8, or 9', regex='^[6-9]\\d{9}$')])),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
                'db_table': 'users',
            },
        ),
    ]
