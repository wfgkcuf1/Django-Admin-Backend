"""
自定义中间件 — 请求/响应处理的钩子链。

知识点:
  1. 中间件函数签名: `__init__(get_response)` + `__call__(request)`
  2. `process_view`: 视图调用前
  3. `process_exception`: 异常处理
  4. `process_template_response`: 模板响应处理
  5. 中间件顺序在 settings.MIDDLEWARE 中定义
  6. 线程安全: `threading.local` 存请求级别的上下文
  7. `contextlib.contextmanager` 生成器中间件写法
"""
import time
import logging
import threading
from typing import Any, Callable, Optional

from django.http import HttpRequest, HttpResponse
from django.utils import timezone

logger = logging.getLogger(__name__)

# ─── 线程本地存储 ────────────────────────────────────────────
# 知识点: threading.local 创建线程独立存储空间
_request_context = threading.local()


def get_current_request() -> Optional[HttpRequest]:
    """
    获取当前线程的请求对象（可在任何地方调用）。

    知识点:
      - getattr: 安全获取属性，不存在返回 None
      - threading.local: 每个线程的局部命名空间
    """
    return getattr(_request_context, "request", None)


def get_current_user():
    """获取当前请求的用户。"""
    request = get_current_request()
    if request:
        return getattr(request, "user", None)
    return None


# ─── 基础中间件类 ────────────────────────────────────────────
class RequestLogMiddleware:
    """
    请求日志中间件 — 记录每个 API 请求。

    知识点:
      - __init__: 服务器启动时调用一次
      - __call__: 每次请求调用
      - get_response(request): 调用下一个中间件或视图
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # ─── 请求前 ────────────────────────────────────────
        # 知识点: 存储请求到线程局部变量
        _request_context.request = request
        request.start_time = time.time()

        # 知识点: f-string 调试语法
        logger.info(
            f"→ {request.method} {request.get_full_path()} "
            f"[{request.META.get('REMOTE_ADDR', 'unknown')}]"
        )

        # ─── 处理请求 ──────────────────────────────────────
        response = self.get_response(request)

        # ─── 请求后 ────────────────────────────────────────
        duration = time.time() - request.start_time
        logger.info(
            f"← {request.method} {request.get_full_path()} "
            f"{response.status_code} ({duration:.3f}s)"
        )

        # 清理线程局部变量
        if hasattr(_request_context, "request"):
            del _request_context.request

        return response


class ResponseTimeMiddleware:
    """
    响应时间中间件 — 给响应添加 X-Response-Time 头。

    知识点:
      - response[header] = value: 设置响应头
      - f"{value:.2f}": 格式化浮点数
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = time.time()
        response = self.get_response(request)
        duration = time.time() - start

        # 设置响应头（毫秒）
        response["X-Response-Time"] = f"{duration * 1000:.2f}ms"
        return response


class HealthCheckMiddleware:
    """
    健康检查中间件 — /health/ 端点不经过其他逻辑。

    知识点:
      - 提前返回 response，不再走后续中间件
      - 状态码 200 + JSON 响应
      - Content-Type 设置
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path == "/health/":
            import json
            from django.db import connection

            # 检查数据库连接
            db_ok = True
            try:
                connection.ensure_connection()
            except Exception:
                db_ok = False

            # 知识点: json.dumps + HttpResponse 手动构造 JSON 响应
            body = json.dumps({
                "status": "healthy" if db_ok else "degraded",
                "database": "ok" if db_ok else "error",
                "timestamp": timezone.now().isoformat(),
            })
            return HttpResponse(
                body,
                content_type="application/json",
                status=200 if db_ok else 503,
            )

        return self.get_response(request)


# ─── 上下文管理器形式 ────────────────────────────────────────
# 知识点: 如果只需要处理 request/response，可以用更简单的函数形式
from django.utils.deprecation import MiddlewareMixin


class SimpleCORSMiddleware(MiddlewareMixin):
    """
    简化版 CORS 中间件（仅演示 MiddlewareMixin 用法）。

    知识点:
      - MiddlewareMixin: 兼容新旧两种中间件写法
      - process_response: 只在响应阶段处理
    """

    def process_response(
        self,
        request: HttpRequest,
        response: HttpResponse,
    ) -> HttpResponse:
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response
