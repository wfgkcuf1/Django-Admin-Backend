"""
文章管理模型 — 多表关联演示。

知识点:
  1. ForeignKey: 外键（多对一）
  2. ManyToManyField: 多对多
  3. related_name: 反向关联名
  4. ordering: 默认排序
  5. 自定义 save() 逻辑
"""
from django.db import models
from django.utils import timezone

from common.base_model import BaseModel, TimestampMixin
from common.enums import ArticleStatus


class Category(BaseModel):
    """文章分类 — 自关联树形结构。"""

    name = models.CharField(verbose_name="分类名称", max_length=100)
    slug = models.SlugField(verbose_name="标识", max_length=100, unique=True)
    description = models.TextField(verbose_name="描述", blank=True, default="")
    sort_order = models.IntegerField(verbose_name="排序", default=0)
    parent = models.ForeignKey(
        "self",
        verbose_name="父分类",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )

    class Meta:
        db_table = "cms_category"
        verbose_name = "文章分类"
        verbose_name_plural = "文章分类"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class Tag(BaseModel):
    """文章标签。"""

    name = models.CharField(verbose_name="标签名称", max_length=50, unique=True)
    color = models.CharField(verbose_name="颜色", max_length=7, default="#1890ff")
    sort_order = models.IntegerField(verbose_name="排序", default=0)

    class Meta:
        db_table = "cms_tag"
        verbose_name = "标签"
        verbose_name_plural = "标签"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class Article(BaseModel):
    """文章。"""

    title = models.CharField(verbose_name="标题", max_length=200)
    slug = models.SlugField(verbose_name="URL 标识", max_length=200, unique=True)
    summary = models.TextField(verbose_name="摘要", blank=True, default="")
    content = models.TextField(verbose_name="内容")
    content_html = models.TextField(verbose_name="渲染后内容", blank=True, default="")
    cover_image = models.URLField(verbose_name="封面图", max_length=500, blank=True, default="")
    status = models.CharField(
        verbose_name="状态",
        max_length=20,
        choices=[(s.value, s.name) for s in ArticleStatus],
        default=ArticleStatus.DRAFT.value,
        db_index=True,
    )
    published_at = models.DateTimeField(verbose_name="发布时间", null=True, blank=True)
    view_count = models.IntegerField(verbose_name="浏览量", default=0)
    like_count = models.IntegerField(verbose_name="点赞数", default=0)
    comment_count = models.IntegerField(verbose_name="评论数", default=0)
    is_top = models.BooleanField(verbose_name="是否置顶", default=False)
    is_recommended = models.BooleanField(verbose_name="是否推荐", default=False)

    # 关联
    category = models.ForeignKey(
        Category,
        verbose_name="分类",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name="标签",
        blank=True,
        related_name="articles",
    )

    class Meta:
        db_table = "cms_article"
        verbose_name = "文章"
        verbose_name_plural = "文章列表"
        ordering = ["-is_top", "-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "published_at"]),
            models.Index(fields=["is_recommended", "-view_count"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        """保存时自动设置发布时间。"""
        if self.status == ArticleStatus.PUBLISHED.value and not self.published_at:
            self.published_at = timezone.now()
        # 可以在这里做 markdown → html 转换
        super().save(*args, **kwargs)

    def increment_view(self) -> None:
        """增加浏览量。"""
        # 知识点: F() 表达式 — 原子递增
        from django.db.models import F
        Article.objects.filter(pk=self.pk).update(view_count=F("view_count") + 1)
        self.view_count += 1
