# Generated by Django 2.2.2 on 2019-06-10 13:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backups', '0005_auto_20190610_1024'),
    ]

    operations = [
        migrations.AlterField(
            model_name='log',
            name='backup_name',
            field=models.CharField(max_length=200),
        ),
    ]