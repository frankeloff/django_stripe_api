# Generated by Django 4.1.6 on 2023-02-13 11:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stripe_api', '0005_rename_count_order_nmb'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='nmb',
            field=models.PositiveIntegerField(verbose_name='Количество'),
        ),
    ]
