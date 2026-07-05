"""
自定义异常层次结构 + DRF 异常处理器。

知识点:
  1. 自定义异常继承链 — `BaseException` → `Exception` → 业务异常
  2. `__init_subclass__` — 子类创建时自动注册
  3. `__cause__` / `__context__` — 异常链（PEP 3134）
  4. `raise ... from ...` — 显式异常链
  5. `sys.exc_info()` — 获取当前异常信息
"""
import logging
import traceback
from typing import Any, Optional

from django.http import Http404
from django.core.exceptions import PermissionDenied
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class AppException(Exception):
    """
    应用异常基类 — 所有业务异常都继承此类。

    知识点:
      - `__init_subclass__` 自动注册子类（类似工厂模式）
      - `**extra` 接受任意额外参数
    """
    _registry: dict[str, type["AppException"]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """子类创建时自动注册到 _registry。"""
        super().__init_subclass__(**kwargs)
        if not cls.__name__.startswith("_"):
            # 知识点: cls.__name__ 是异常的类名
            AppException._registry[cls.__name__] = cls

    def __init__(
        self,
        message: str = "应用异常",
        code: int = 500,
        errors: Optional[list[dict[str, Any]]] = None,
        **extra: Any,
    ) -> None:
        self.message = message
        self.code = code
        self.errors = errors or []
        self.extra = extra
        super().__init__(self.message)


class BusinessError(AppException):
    """业务逻辑错误——可用预期错误，如参数校验失败。"""
    def __init__(
        self,
        message: str = "业务逻辑错误",
        code: int = 400,
        **kwargs: Any,
    ) -> None:
        super().__init__(message=message, code=code, **kwargs)


class ResourceNotFound(AppException):
    """资源不存在（404）。"""
    def __init__(
        self,
        message: str = "请求的资源不存在",
        resource_type: Optional[str] = None,
        resource_id: Any = None,
        **kwargs: Any,
    ) -> None:
        detail = message
        if resource_type and resource_id:
            detail = f"{resource_type}(id={resource_id}) 不存在"
        super().__init__(message=detail, code=404, **kwargs)


class PermissionDeniedError(AppException):
    """权限不足（403）。"""
    def __init__(
        self,
        message: str = "没有执行此操作的权限",
        required_permission: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message=message, code=403, **kwargs)


class AuthenticationError(AppException):
    """认证失败（401）。"""
    def __init__(self, message: str = "身份验证失败", **kwargs: Any) -> None:
        super().__init__(message=message, code=401, **kwargs)


class ConflictError(AppException):
    """资源冲突（409）。"""
    def __init__(self, message: str = "资源冲突", **kwargs: Any) -> None:
        super().__init__(message=message, code=409, **kwargs)


class ValidationError(AppException):
    """数据验证失败（422）。"""
    def __init__(
        self,
        message: str = "数据验证失败",
        errors: Optional[list[dict]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message=message, code=422, errors=errors, **kwargs)


class RateLimitError(AppException):
    """请求频率超限（429）。"""
    def __init__(self, message: str = "请求频率超限，请稍后再试", **kwargs: Any) -> None:
        super().__init__(message=message, code=429, **kwargs)


# ─── DRF 异常处理器 ──────────────────────────────────────────
def custom_exception_handler(exc: Exception, context: dict) -> Optional[Response]:
    """
    自定义异常处理器 — 替换 DRF 默认的错误格式。

    知识点:
      - 高阶函数: exception_handler 接收异常和上下文，返回 Response
      - `isinstance(exc, SomeException)`: 按类型判断
      - 异常链: `raise ... from exc`
    """
    # 先调用 DRF 默认处理器
    response = drf_exception_handler(exc, context)

    # ─── 处理我们的自定义异常 ────────────────────────────────
    if isinstance(exc, AppException):
        return Response(
            {
                "code": exc.code,
                "message": exc.message,
                "errors": exc.errors,
                "data": None,
            },
            status=exc.code,
        )

    # ─── 处理 Django 内置异常 ────────────────────────────────
    if isinstance(exc, Http404):
        return Response(
            {"code": 404, "message": "资源不存在", "data": None},
            status=404,
        )

    if isinstance(exc, PermissionDenied):
        return Response(
            {"code": 403, "message": "权限不足", "data": None},
            status=403,
        )

    # ─── 处理未预料的异常（500） ─────────────────────────────
    if response is None:
        logger.critical(
            f"未处理的异常:\n{traceback.format_exc()}"
        )
        return Response(
            {"code": 500, "message": "服务器内部错误", "data": None},
            status=500,
        )

    return response
