# Generated by Django 2.0.3 on 2018-06-06 13:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_auto_20180606_2141'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userinfo',
            name='gender',
            field=models.CharField(choices=[('M', 'Male'), ('F', 'Female')], default='Male', max_length=6),
        ),
    ]
