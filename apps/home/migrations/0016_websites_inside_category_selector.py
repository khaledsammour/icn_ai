# Generated by Django 4.2.9 on 2024-10-10 08:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0015_auto_20241008_0930'),
    ]

    operations = [
        migrations.AddField(
            model_name='websites',
            name='inside_category_selector',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
