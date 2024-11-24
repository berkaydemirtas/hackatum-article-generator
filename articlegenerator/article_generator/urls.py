from rest_framework.routers import DefaultRouter
from .views import NewsViewSet, ArticleViewSet, ImageViewSet

router = DefaultRouter()
router.register(r'news', NewsViewSet, basename='news')
router.register(r'articles', ArticleViewSet, basename='articles')
router.register(r'images', ImageViewSet, basename='images')



urlpatterns = router.urls