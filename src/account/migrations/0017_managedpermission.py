# Generated by Django 2.2.20 on 2021-04-19 10:21

from django.db import migrations, models
import django.db.models.manager
import django_grainy.fields
import django_handleref.models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0016_alter_foreign_keys'),
    ]

    operations = [
        migrations.CreateModel(
            name='ManagedPermission',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('created', django_handleref.models.CreatedDateTimeField(auto_now_add=True, verbose_name='Created')),
                ('updated', django_handleref.models.UpdatedDateTimeField(auto_now=True, verbose_name='Updated')),
                ('version', models.IntegerField(default=0)),
                ('status', models.CharField(choices=[('ok', 'Ok'), ('pending', 'Pending'), ('deactivated', 'Deactivated'), ('failed', 'Failed'), ('expired', 'Expired')], default='ok', max_length=12)),
                ('namespace', models.CharField(help_text='The permission namespace. The following variables are available for formatting: {org_id}', max_length=255)),
                ('group', models.CharField(help_text='Belongs to this group of permissions', max_length=255)),
                ('description', models.CharField(help_text='What is this permission namespace used for?', max_length=255)),
                ('managable', models.BooleanField(default=True, help_text='Can organization admins manage this permission?')),
                ('auto_grant_admins', django_grainy.fields.PermissionField(help_text='Auto grants the permission at the following level to organization admins')),
                ('auto_grant_users', django_grainy.fields.PermissionField(help_text='Auto grants the permission at the following level to organization members')),
            ],
            options={
                'verbose_name': 'Custom permission',
                'verbose_name_plural': 'Custom permissions',
                'db_table': 'account_managed_permission',
            },
            managers=[
                ('handleref', django.db.models.manager.Manager()),
            ],
        ),
    ]
