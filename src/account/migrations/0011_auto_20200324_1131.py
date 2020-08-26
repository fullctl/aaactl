# Generated by Django 2.2.11 on 2020-03-24 11:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("account", "0010_invitation")]

    operations = [
        migrations.AddField(
            model_name="invitation",
            name="redirect",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="apikey",
            name="status",
            field=models.CharField(
                choices=[
                    ("ok", "Ok"),
                    ("pending", "Pending"),
                    ("deactivated", "Deactivated"),
                    ("failed", "Failed"),
                    ("expired", "Expired"),
                ],
                default="ok",
                max_length=12,
            ),
        ),
        migrations.AlterField(
            model_name="apikeypermission",
            name="status",
            field=models.CharField(
                choices=[
                    ("ok", "Ok"),
                    ("pending", "Pending"),
                    ("deactivated", "Deactivated"),
                    ("failed", "Failed"),
                    ("expired", "Expired"),
                ],
                default="ok",
                max_length=12,
            ),
        ),
        migrations.AlterField(
            model_name="invitation",
            name="status",
            field=models.CharField(
                choices=[
                    ("ok", "Ok"),
                    ("pending", "Pending"),
                    ("deactivated", "Deactivated"),
                    ("failed", "Failed"),
                    ("expired", "Expired"),
                ],
                default="ok",
                max_length=12,
            ),
        ),
        migrations.AlterField(
            model_name="organization",
            name="status",
            field=models.CharField(
                choices=[
                    ("ok", "Ok"),
                    ("pending", "Pending"),
                    ("deactivated", "Deactivated"),
                    ("failed", "Failed"),
                    ("expired", "Expired"),
                ],
                default="ok",
                max_length=12,
            ),
        ),
        migrations.AlterField(
            model_name="organizationuser",
            name="status",
            field=models.CharField(
                choices=[
                    ("ok", "Ok"),
                    ("pending", "Pending"),
                    ("deactivated", "Deactivated"),
                    ("failed", "Failed"),
                    ("expired", "Expired"),
                ],
                default="ok",
                max_length=12,
            ),
        ),
        migrations.AlterField(
            model_name="usersettings",
            name="status",
            field=models.CharField(
                choices=[
                    ("ok", "Ok"),
                    ("pending", "Pending"),
                    ("deactivated", "Deactivated"),
                    ("failed", "Failed"),
                    ("expired", "Expired"),
                ],
                default="ok",
                max_length=12,
            ),
        ),
    ]
