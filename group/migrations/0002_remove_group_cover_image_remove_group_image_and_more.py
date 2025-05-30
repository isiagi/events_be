# Generated by Django 4.2.20 on 2025-05-21 18:00

import cloudinary.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='group',
            name='cover_image',
        ),
        migrations.RemoveField(
            model_name='group',
            name='image',
        ),
        migrations.AddField(
            model_name='group',
            name='slug',
            field=models.SlugField(blank=True, max_length=255, null=True, unique=True),
        ),
        migrations.CreateModel(
            name='GroupImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', cloudinary.models.CloudinaryField(max_length=255, verbose_name='image')),
                ('is_cover', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='group.group')),
            ],
            options={
                'ordering': ['-is_cover', '-created_at'],
            },
        ),
    ]
