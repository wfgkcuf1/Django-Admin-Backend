"""
仪表盘视图 — 统计数据聚合。

知识点:
  1. APIView: 非 CRUD 视图
  2. aggregate(): 聚合查询（Sum, Count, Avg）
  3. annotate(): 分组聚合
  4. TruncDate/TruncMonth: 时间截断函数
  5. cache.set / cache.get 缓存聚合结果
"""
from datetime import timedelta

from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from common.decorators import cached
from common.response import ok


class DashboardView(APIView):
    """
    仪表盘聚合数据。

    知识点:
      - APIView: 不使用 ViewSet 的场景
      - CacheService.get_or_set: 缓存聚合结果
      - aggregate / annotate: Django ORM 聚合
    """

    permission_classes = [IsAdminUser]
    cache_timeout = 300  # 5 分钟

    def get(self, request):
        """获取仪表盘数据。"""
        from common.cache import CacheService

        data = CacheService.get_or_set(
            "dashboard:stats",
            self._get_stats,
            self.cache_timeout,
        )
        return ok(data=data)

    def _get_stats(self) -> dict:
        """聚合统计数据。"""
        from apps.users.models import User
        from apps.articles.models import Article
        from apps.orders.models import Order
        from apps.logs.models import OperationLog

        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        return {
            "users": {
                "total": User.objects.active().count(),
                "new_today": User.objects.filter(
                    date_joined__gte=today_start
                ).count(),
                "new_week": User.objects.filter(
                    date_joined__gte=week_ago
                ).count(),
            },
            "articles": {
                "total": Article.objects.filter(
                    deleted_at__isnull=True
                ).count(),
                "published": Article.objects.filter(
                    status="published"
                ).count(),
                "drafts": Article.objects.filter(status="draft").count(),
            },
            "orders": {
                "total": Order.objects.count(),
                "total_amount": str(
                    Order.objects.aggregate(
                        total=Sum("pay_amount")
                    )["total"] or 0
                ),
                "today_amount": str(
                    Order.objects.filter(
                        created_at__gte=today_start
                    ).aggregate(total=Sum("pay_amount"))["total"] or 0
                ),
                "pending": Order.objects.filter(status="pending").count(),
            },
            "operations": {
                "total": OperationLog.objects.count(),
                "today": OperationLog.objects.filter(
                    created_at__gte=today_start
                ).count(),
            },
        }
