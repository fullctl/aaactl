# Generated by Django 3.2.23 on 2024-04-13 01:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('whitelabel_fullctl', '0002_auto_20240412_1928'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organizationwhitelabeling',
            name='dark_logo_url',
            field=models.URLField(blank=True, help_text='URL used to display the dark logo on the dashboard.', max_length=2000, null=True, verbose_name='Logo URL'),
        ),
        migrations.AlterField(
            model_name='organizationwhitelabeling',
            name='light_logo_url',
            field=models.URLField(blank=True, help_text='URL used to display the light logo on the dashboard.', max_length=2000, null=True, verbose_name='Logo URL'),
        ),
    ]
