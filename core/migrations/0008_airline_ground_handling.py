# Generated by Django 2.0.5 on 2018-05-26 16:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_auto_20180526_1633'),
    ]

    operations = [
        migrations.AddField(
            model_name='airline',
            name='ground_handling',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.GroundHandling'),
        ),
    ]
