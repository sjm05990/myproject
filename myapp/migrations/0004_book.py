# Generated by Django 3.0 on 2020-10-08 07:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0003_user_usertype'),
    ]

    operations = [
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('book_category', models.CharField(choices=[('python', 'python'), ('java', 'java'), ('php', 'php')], default='', max_length=200)),
                ('book_name', models.CharField(max_length=100)),
                ('book_author', models.CharField(max_length=100)),
                ('book_price', models.CharField(max_length=100)),
                ('book_desc', models.TextField()),
                ('book_image', models.ImageField(default='', upload_to='books/')),
            ],
        ),
    ]
