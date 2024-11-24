# Generated by Django 4.2 on 2024-11-23 13:06

from django.db import migrations, models
import pgvector.django.vector


class Migration(migrations.Migration):

    dependencies = [
        ('article_generator', '0003_article_cluster_news_created_at_alter_news_link_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cluster',
            name='centroid',
            field=pgvector.django.vector.VectorField(dimensions=1536, null=True),
        ),
        migrations.AlterField(
            model_name='article',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]