# Generated by Django 3.0 on 2020-10-13 04:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0005_book_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='book_category',
            field=models.CharField(choices=[('python', 'python'), ('java', 'java'), ('php', 'php'), ('C', 'C')], default='', max_length=200),
        ),
    ]
