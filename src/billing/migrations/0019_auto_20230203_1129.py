# Generated by Django 3.2.16 on 2023-02-03 11:29

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0018_product_renewable"),
    ]

    operations = [
        migrations.AlterField(
            model_name="recurringproduct",
            name="price",
            field=models.DecimalField(
                decimal_places=2,
                default=0.0,
                help_text="Price for recurring product charges. For fixed pricing this is the total price charged each subscription cycle. For metered unit this would be the usage price per unit.",
                max_digits=6,
            ),
        ),
        migrations.AlterField(
            model_name="recurringproduct",
            name="type",
            field=models.CharField(
                choices=[("fixed", "Fixed Price"), ("metered", "Metered Unit Price")],
                default=None,
                max_length=255,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="recurringproduct",
            name="unit",
            field=models.CharField(
                default="Unit",
                help_text="Label for a unit in the context of metered usage",
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="recurringproduct",
            name="unit_plural",
            field=models.CharField(
                default="Units",
                help_text="Label for multiple units in the context of metered usage",
                max_length=40,
            ),
        ),
    ]
