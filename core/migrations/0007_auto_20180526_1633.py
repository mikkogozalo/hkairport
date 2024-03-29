# Generated by Django 2.0.5 on 2018-05-26 16:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20180526_1616'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='airlineaisle',
            unique_together={('airline', 'aisle')},
        ),
        migrations.AlterUniqueTogether(
            name='airlinelounge',
            unique_together={('airline', 'lounge')},
        ),
        migrations.AlterUniqueTogether(
            name='airlinetransferdesk',
            unique_together={('airline', 'transfer_desk')},
        ),
        migrations.AlterUniqueTogether(
            name='loungephone',
            unique_together={('lounge', 'phone')},
        ),
    ]
