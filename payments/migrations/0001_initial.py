# Generated by Django 5.2.3 on 2025-07-09 06:01

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('razorpay_order_id', models.CharField(max_length=100, unique=True)),
                ('razorpay_payment_id', models.CharField(blank=True, max_length=100, null=True)),
                ('razorpay_signature', models.CharField(blank=True, max_length=200, null=True)),
                ('amount', models.IntegerField()),
                ('currency', models.CharField(default='INR', max_length=3)),
                ('status', models.CharField(choices=[('created', 'Created'), ('authorized', 'Authorized'), ('captured', 'Captured'), ('refunded', 'Refunded'), ('failed', 'Failed')], default='created', max_length=20)),
                ('receipt', models.CharField(max_length=100)),
                ('notes', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'payments',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('active', 'Active'), ('expired', 'Expired'), ('cancelled', 'Cancelled')], default='active', max_length=20)),
                ('starts_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('expires_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='payments.payment')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'subscriptions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['user', '-created_at'], name='payments_user_id_2c5fd7_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['razorpay_order_id'], name='payments_razorpa_c67522_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['status'], name='payments_status_d621e5_idx'),
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['user'], name='subscriptio_user_id_aa8bc6_idx'),
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['status'], name='subscriptio_status_572d44_idx'),
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['expires_at'], name='subscriptio_expires_af5d7e_idx'),
        ),
    ]
