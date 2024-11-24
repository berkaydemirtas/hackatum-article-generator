import os
import base64
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import News, Article, Image
from .serializers import NewsSerializer, NewsDetailSerializer, ArticleSerializer, ImageSerializer

class NewsViewSet(ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return NewsDetailSerializer
        return NewsSerializer
    
class ArticleViewSet(ModelViewSet):
    queryset = Article.objects.all().order_by('-created_at')
    serializer_class = ArticleSerializer
    
class ImageViewSet(ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

    @action(detail=True, methods=['get'], url_path='download')
    def download_image(self, request, pk=None):
        """
        Endpoint to download an image by its ID.
        """
        image = get_object_or_404(Image, id=pk)

        # Generate a user-friendly filename with classification
        response = HttpResponse(image.file_data, content_type='image/jpeg')
        response['Content-Disposition'] = f'inline; filename="{image.classification}.jpg"'
        return response