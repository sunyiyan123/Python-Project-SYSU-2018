# Generated by Django 2.0.3 on 2018-06-20 21:27

from django.db import migrations
import imagekit.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('lenotes', '0008_remove_diary_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='profile',
            field=imagekit.models.fields.ProcessedImageField(default='group/img/default.jpg', upload_to='group/img'),
        ),
    ]
