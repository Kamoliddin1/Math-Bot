# Generated by Django 3.2.4 on 2021-07-12 10:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0003_profile_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='user_spend',
            field=models.FloatField(default=0.0),
        ),
    ]