# Generated by Django 4.2.9 on 2024-11-19 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0025_websites_change_content'),
    ]

    operations = [
        migrations.AddField(
            model_name='websites',
            name='inner_selector',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='websites',
            name='not_contains_class',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
