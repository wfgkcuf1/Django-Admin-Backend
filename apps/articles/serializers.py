from rest_framework import serializers
from common.base_serializer import BaseModelSerializer
from common.enums import ArticleStatus
from .models import Article, Category, Tag
from apps.users.serializers import UserListSerializer


class TagSerializer(BaseModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class CategorySerializer(BaseModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = "__all__"

    def get_children(self, obj):
        children = obj.children.all()
        if children:
            return CategorySerializer(children, many=True).data
        return []


class ArticleListSerializer(BaseModelSerializer):
    category_name = serializers.SerializerMethodField()
    tags_list = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "id", "title", "summary", "cover_image", "status", "status_label",
            "category", "category_name", "tags", "tags_list",
            "is_top", "is_recommended",
            "view_count", "like_count", "comment_count",
            "published_at", "created_at", "updated_at",
            "author_name",
        ]

    def get_category_name(self, obj) -> str:
        return obj.category.name if obj.category else ""

    def get_tags_list(self, obj):
        return [{"id": t.id, "name": t.name} for t in obj.tags.all()]

    def get_author_name(self, obj) -> str:
        return obj.created_by.display_name if obj.created_by else ""

    def get_status_label(self, obj) -> str:
        try:
            return ArticleStatus(obj.status).name
        except ValueError:
            return obj.status


class ArticleDetailSerializer(ArticleListSerializer):
    content = serializers.CharField()

    class Meta(ArticleListSerializer.Meta):
        fields = ArticleListSerializer.Meta.fields + ["content", "content_html"]
