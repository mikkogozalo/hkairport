# Generated by Django 2.0.5 on 2018-05-26 22:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_auto_20180527_0611'),
    ]

    operations = [
        migrations.AddField(
            model_name='arrival',
            name='is_cargo',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='departure',
            name='is_cargo',
            field=models.BooleanField(default=False),
        ),
    ]
