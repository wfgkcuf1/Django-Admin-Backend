"""
操作日志视图 — 查询日志（只读）。

知识点:
  - 日志视图只读: 不提供 create/update/destroy
  - 可以自定义 ReadOnlyModelViewSet
"""
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAdminUser

from common.pagination import StandardPagination
from .models import OperationLog
from .serializers import OperationLogSerializer


class OperationLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    操作日志视图（只读）。

    知识点:
      - 只继承 List + Retrieve Mixin，没有 Create/Update/Destroy
      - 仅管理员可查看
    """
    queryset = OperationLog.objects.all()
    serializer_class = OperationLogSerializer
    permission_classes = [IsAdminUser]
    pagination_class = StandardPagination
    ordering = "-created_at"
    search_fields = ["username", "action", "model_name", "detail"]
    filterset_fields = ["action", "model_name", "user", "status"]
