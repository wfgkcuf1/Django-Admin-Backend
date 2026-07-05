from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from common.base_view import BaseViewSet
from common.response import ok
from common.enums import ArticleStatus
from .models import Article, Category, Tag
from .serializers import (
    ArticleListSerializer, ArticleDetailSerializer,
    CategorySerializer, TagSerializer,
)


class ArticleViewSet(BaseViewSet):
    queryset = Article.objects.filter(
        deleted_at__isnull=True, is_active=True
    )
    search_fields = ["title", "summary", "content"]
    ordering_fields = ["created_at", "published_at", "view_count", "like_count"]
    ordering = "-published_at"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ArticleDetailSerializer
        return ArticleListSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        article = self.get_object()
        article.status = ArticleStatus.PUBLISHED.value
        article.save()
        return ok(message="文章已发布")

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        article = self.get_object()
        article.status = ArticleStatus.ARCHIVED.value
        article.save()
        return ok(message="文章已归档")

    @action(detail=True, methods=["post"])
    def increment_view(self, request, pk=None):
        article = self.get_object()
        article.increment_view()
        return ok(data={"view_count": article.view_count})


class CategoryViewSet(BaseViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    search_fields = ["name"]


class TagViewSet(BaseViewSet):
    queryset = Tag.objects.filter(is_active=True)
    serializer_class = TagSerializer
    search_fields = ["name"]
