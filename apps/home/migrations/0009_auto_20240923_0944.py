# Generated by Django 3.2.16 on 2024-09-23 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0008_auto_20240923_0840'),
    ]

    operations = [
        migrations.AddField(
            model_name='websites',
            name='end_index',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='websites',
            name='start_index',
            field=models.IntegerField(blank=True, default=1, null=True),
        ),
    ]
