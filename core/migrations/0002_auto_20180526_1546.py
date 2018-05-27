# Generated by Django 2.0.5 on 2018-05-26 15:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoungePhone',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(max_length=64)),
                ('is_fax', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'lounge_phone',
            },
        ),
        migrations.CreateModel(
            name='Terminal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.CharField(db_index=True, max_length=64)),
                ('full_name', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'db_table': 'terminal',
            },
        ),
        migrations.AddField(
            model_name='lounge',
            name='location',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='lounge',
            name='opening_hours',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='lounge',
            name='remark',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='airline',
            name='iata',
            field=models.CharField(default='A', max_length=2, unique=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='airline',
            name='icao',
            field=models.CharField(default='A', max_length=3, unique=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='aisle',
            name='name',
            field=models.CharField(db_index=True, max_length=1),
        ),
        migrations.AddField(
            model_name='loungephone',
            name='lounge',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='phones', to='core.Lounge'),
        ),
    ]
