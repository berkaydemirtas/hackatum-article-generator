from rest_framework import serializers
from .models import News, Article, Cluster, Image

class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['id', 'title', 'link', 'description', 'created_at']

class NewsDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['id', 'title', 'link', 'description', 'content', 'created_at', 'cluster']

class ArticleSerializer(serializers.ModelSerializer):
    main_image = serializers.SerializerMethodField()
    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'created_at', 'used_news', 'confidence_score', 'main_image']

    def get_main_image(self, obj):
        image = obj.images.all().first()
        if image:
            return f'http://localhost:8000/images/{image.id}/download/'
        return None

    
class ImageSerializer(serializers.ModelSerializer):
    classification_display = serializers.CharField(source='get_classification_display', read_only=True)

    class Meta:
        model = Image
        fields = ['id', 'classification', 'classification_display']
    

class ClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cluster
        fields = ['id']
