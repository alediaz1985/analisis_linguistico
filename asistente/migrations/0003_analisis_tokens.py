# Generated by Django 5.1.3 on 2024-11-18 14:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asistente', '0002_alter_analisis_categorias_lexicas_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='analisis',
            name='tokens',
            field=models.JSONField(default=list),
        ),
    ]
