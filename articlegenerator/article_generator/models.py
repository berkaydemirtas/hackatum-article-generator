from django.db import models
from pgvector.django import VectorField, CosineDistance
from django.db.models import F



class Cluster(models.Model):

    centroid = VectorField(dimensions=1536, null=True)
    def __str__(self):
        return f"Cluster {self.id}"
    
class News(models.Model):
    title = models.CharField(max_length=255)
    link = models.URLField(unique=True)
    description = models.TextField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    embedding = VectorField(dimensions=1536)  
    cluster = models.ForeignKey(Cluster, on_delete=models.SET_NULL, null=True)
    published_at = models.DateTimeField(null=True)

    def __str__(self):
        return self.title
    
    def get_closest_cluster(self):
        from article_generator.models import Cluster  
        closest_cluster = (
            Cluster.objects.annotate(similarity=(1-CosineDistance("centroid", self.embedding)))
            .order_by("similarity")
            .first()
        )
        return closest_cluster, closest_cluster.similarity
    
 
class Image(models.Model):
    class Classification(models.IntegerChoices):
        MAIN = 0, "Main"
        SCORE = 1, "Score"

    file_data = models.BinaryField()  
    classification = models.IntegerField(choices=Classification.choices)

    def __str__(self):
        return f"Image ({self.id()})"


class Article(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    used_news = models.ManyToManyField(News, null=True)
    confidence_score = models.FloatField(default=0.0)
    images = models.ManyToManyField(Image, blank=True)

    def __str__(self):
        return self.title
