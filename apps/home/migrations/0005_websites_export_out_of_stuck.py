# Generated by Django 3.2.16 on 2024-09-23 08:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0004_auto_20240923_0749'),
    ]

    operations = [
        migrations.AddField(
            model_name='websites',
            name='export_out_of_stuck',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
