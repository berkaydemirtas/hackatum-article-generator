# Generated by Django 4.2 on 2024-11-23 17:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('article_generator', '0006_article_confidence_score_article_used_news'),
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_data', models.BinaryField()),
                ('classification', models.IntegerField(choices=[(0, 'Main'), (1, 'Score')])),
            ],
        ),
        migrations.AddField(
            model_name='article',
            name='images',
            field=models.ManyToManyField(blank=True, to='article_generator.image'),
        ),
    ]
