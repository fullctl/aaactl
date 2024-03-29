# Generated by Django 3.2.14 on 2022-07-13 16:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0008_reftag_pass_1"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="price",
            field=models.DecimalField(
                decimal_places=2,
                default=0.0,
                help_text="Price charge on initial setup / purchase. For recurring_product pricing this could specify a setup fee. For non-recurring_product pricing, this is the product price.",
                max_digits=6,
            ),
        ),
        migrations.AlterField(
            model_name="recurringproduct",
            name="data",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Arbitrary extra data you want to define for this recurring_product product",
            ),
        ),
        migrations.AlterField(
            model_name="recurringproduct",
            name="price",
            field=models.DecimalField(
                decimal_places=2,
                default=0.0,
                help_text="Price in the context of recurring_product charges. For fixed recurring_product pricing this would be the price charged each cycle. For metered pricing this would be the usage price per metered unit.",
                max_digits=6,
            ),
        ),
        migrations.AlterField(
            model_name="recurringproduct",
            name="product",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="recurring_product",
                to="billing.product",
            ),
        ),
        migrations.AlterField(
            model_name="subscriptioncycleproduct",
            name="subproduct",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cycleproduct_set",
                to="billing.subscriptionproduct",
            ),
        ),
    ]
