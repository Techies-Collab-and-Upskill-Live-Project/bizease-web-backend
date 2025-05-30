# Generated by Django 5.2.1 on 2025-05-14 10:42

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('business_name', models.CharField(max_length=200, unique=True)),
                ('full_name', models.CharField(max_length=200)),
                ('email', models.CharField(max_length=150, unique=True)),
                ('business_email', models.CharField(blank=True, max_length=150, null=True, unique=True)),
                ('currency', models.CharField(choices=[('USD', 'United States dollar'), ('NGN', 'Nigerian naira'), ('GBP', 'Pound sterling')], default='NGN', max_length=3)),
                ('business_type', models.CharField(blank=True, max_length=150)),
                ('password', models.CharField(max_length=50)),
                ('country', models.CharField(choices=[('United States', 'United States'), ('Nigeria', 'Nigeria')])),
                ('state', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
