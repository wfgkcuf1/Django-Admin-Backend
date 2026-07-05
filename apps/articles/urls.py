from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet, CategoryViewSet, TagViewSet

app_name = "articles"

router = DefaultRouter()
router.register("articles", ArticleViewSet)
router.register("categories", CategoryViewSet)
router.register("tags", TagViewSet)

urlpatterns = [path("", include(router.urls))]
