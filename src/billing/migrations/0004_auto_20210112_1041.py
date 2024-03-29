# Generated by Django 2.2.16 on 2021-01-12 10:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0003_auto_20210112_1021"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productmodifier",
            name="type",
            field=models.CharField(
                choices=[
                    ("reduction", "Price Reduction"),
                    ("reduction_p", "Price Reduction (%)"),
                    ("quantity", "Free Quantity"),
                    ("free", "Free"),
                ],
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="subscriptionproductmodifier",
            name="type",
            field=models.CharField(
                choices=[
                    ("reduction", "Price Reduction"),
                    ("reduction_p", "Price Reduction (%)"),
                    ("quantity", "Free Quantity"),
                    ("free", "Free"),
                ],
                max_length=255,
            ),
        ),
    ]
