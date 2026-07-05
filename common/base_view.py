"""
基础视图层 — 所有 API 视图的基类。

知识点:
  1. 类继承 — DRF 的 ModelViewSet → 自定义 BaseModelViewSet
  2. 混入类顺序 — MRO 影响 super() 调用链
  3. `Generic[T]` 类型参数化
  4. `__init_subclass__` 自动注册子类
  5. `__init__` 重写 + super().__init__
"""
import logging
from typing import Any, Optional, TypeVar

from django.db.models import QuerySet, Model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.request import Request
from rest_framework.response import Response

from common.response import ApiResponse, ok, created, fail
from common.exceptions import BusinessError
from common.mixins import ActionLogMixin, ExportMixin

logger = logging.getLogger(__name__)

# 泛型类型变量
M = TypeVar("M", bound=Model)


class BaseViewSet(ActionLogMixin, ExportMixin, viewsets.ModelViewSet):
    """
    基础视图集 — 所有 API 视图的基类。

    继承链:
      ActionLogMixin → ExportMixin → ModelViewSet

    知识点:
      - ModelViewSet 自身继承: CreateModelMixin + RetrieveModelMixin +
        UpdateModelMixin + DestroyModelMixin + ListModelMixin + GenericViewSet
      - 重写 list / create / update / destroy 以使用统一响应格式
    """

    # ─── 可配置的属性 ────────────────────────────────────────
    search_fields: tuple[str, ...] = ()
    ordering_fields: tuple[str, ...] = ()
    ordering: str = "-created_at"
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # 知识点: 初始化时可以进行一些检查
        pass

    # ─── 标准 CRUD 响应重写 ──────────────────────────────────

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        列表查询。

        知识点:
          - super().list() 调用 DRF 原生的列表方法
          - 返回数据在 response.data 中
          - 对分页和非分页分别处理
        """
        try:
            response = super().list(request, *args, **kwargs)

            # 知识点: 检查是否有分页
            if hasattr(self, "paginator") and self.paginator is not None:
                return ApiResponse.success(
                    data=response.data,
                    message="查询成功",
                ).to_response()

            return ok(data=response.data)
        except Exception as e:
            logger.error(f"列表查询失败: {e}", exc_info=True)
            return fail(message=f"查询失败: {str(e)}")

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """创建资源。"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return created(data=serializer.data)
        except Exception as e:
            logger.error(f"创建失败: {e}", exc_info=True)
            return fail(message=f"创建失败: {str(e)}", code=400)

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """查询单个资源。"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return ok(data=serializer.data)
        except Exception as e:
            logger.error(f"查询详情失败: {e}", exc_info=True)
            raise  # 让异常处理器处理

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """更新资源。"""
        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return ok(data=serializer.data, message="更新成功")
        except Exception as e:
            logger.error(f"更新失败: {e}", exc_info=True)
            return fail(message=f"更新失败: {str(e)}", code=400)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """删除资源。"""
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return ApiResponse.no_content(message="删除成功").to_response()
        except Exception as e:
            logger.error(f"删除失败: {e}", exc_info=True)
            return fail(message=f"删除失败: {str(e)}", code=400)

    # ─── 批量操作 ──────────────────────────────────────────
    # 知识点: @action(detail=False) 自定义操作，作用于列表而非单条

    @action(detail=False, methods=["delete"])
    def batch_delete(self, request: Request) -> Response:
        """
        批量删除。

        知识点:
          - request.data.get("ids", []) 获取 ID 列表
          - 列表推导式
          - 事务: @transaction.atomic
        """
        from django.db import transaction

        ids = request.data.get("ids", [])
        if not ids:
            return fail(message="请提供要删除的 ID 列表")

        with transaction.atomic():
            queryset = self.get_queryset().filter(pk__in=ids)
            deleted_count, _ = queryset.delete()

        return ok(data={"deleted_count": deleted_count}, message=f"成功删除 {deleted_count} 条")

    @action(detail=False, methods=["patch"])
    def batch_update(self, request: Request) -> Response:
        """
        批量更新（所有选中记录设为相同值）。

        知识点:
          - ids: 要更新的记录 ID
          - data: 要更新的字段
        """
        from django.db import transaction

        ids = request.data.get("ids", [])
        data = request.data.get("data", {})
        if not ids or not data:
            return fail(message="请提供 ID 列表和更新数据")

        with transaction.atomic():
            queryset = self.get_queryset().filter(pk__in=ids)
            updated_count = queryset.update(**data)

        return ok(
            data={"updated_count": updated_count},
            message=f"成功更新 {updated_count} 条",
        )

    @action(detail=False, methods=["post"])
    def export(self, request: Request) -> Response:
        """
        导出为 Excel。

        知识点:
          - @action 自定义路由
          - HttpResponse 返回文件流
          - Content-Disposition 头控制下载
        """
        from django.http import HttpResponse

        fields = request.data.get("fields", [])
        if not fields:
            return fail(message="请指定要导出的字段")

        queryset = self.filter_queryset(self.get_queryset())
        excel_bytes = self.export_data(queryset, fields)

        response = HttpResponse(
            excel_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="export.xlsx"'
        return response
