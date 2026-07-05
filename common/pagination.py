"""
分页工具 — 标准分页实现。

知识点:
  1. DRF 分页类自定义
  2. `__init_subclass__` 注册机制
  3. 生成器 `yield` 分批处理大量数据
  4. page / size 参数自定义
"""
from typing import Any

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from common.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class StandardPagination(PageNumberPagination):
    """
    标准分页 — 所有列表接口统一使用。

    知识点:
      - page_size: 每页数量
      - page_query_param: 前端传的页码参数名
      - page_size_query_param: 前端传的每页数量参数名
      - max_page_size: 上限保护
    """
    page_size = DEFAULT_PAGE_SIZE
    page_query_param = "page"
    page_size_query_param = "size"
    max_page_size = MAX_PAGE_SIZE

    def get_paginated_response(self, data: list) -> Response:
        """
        自定义分页响应格式。

        返回:
          {
            "total": 100,
            "page": 1,
            "size": 20,
            "total_pages": 5,
            "results": [...]
          }
        """
        return Response({
            "total": self.page.paginator.count,
            "page": self.page.number,
            "size": self.get_page_size(self.request),
            "total_pages": self.page.paginator.num_pages,
            "results": data,
        })


class CursorPaginationMixin:
    """
    游标分页混入类 — 用于大数据集，性能优于偏移分页。

    知识点:
      - 游标分页: 基于排序字段的 WHERE 条件，不 OFFSET
      - 适合实时数据（新数据插入不影响旧数据位置）
      - 缺点是：不支持跳页
    """
    pass  # 预留，需要时实现


def batch_process(queryset, batch_size: int = 500) -> Any:
    """
    分批处理查询集 — 使用生成器减少内存占用。

    知识点:
      - 生成器函数 (yield)
      - queryset.iterator(): 服务端游标，不一次性加载所有数据
      - chunk_size: 每次从数据库读取的条数

    用法:
      for batch in batch_process(User.objects.all()):
          for user in batch:
              process(user)
    """
    # 知识点: iterator() 使用服务端游标，减少内存
    iterator = queryset.iterator(chunk_size=batch_size)

    # 知识点: 无限循环 + 手动 break
    while True:
        batch = []
        try:
            for _ in range(batch_size):
                batch.append(next(iterator))
        except StopIteration:
            # 知识点: 海象运算符
            if batch:
                yield batch
            break

        if batch:
            yield batch
