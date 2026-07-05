"""
统一 API 响应格式 — 所有接口返回标准结构。

知识点:
  - `dataclasses.dataclass` — 数据类（Python 3.7+）
  - `@dataclass(frozen=True)` — 不可变数据类
  - `@property` — 计算属性
  - `classmethod` — 工厂方法
  - `Generic[T]` — 泛型类型标注
  - `OrderedDict` — 有序字典（Python 3.7+ 普通 dict 也有序，但仍保留此种写法）
  - `__init_subclass__` — 子类 Hook
"""
from dataclasses import dataclass, field
from typing import Any, Generic, Optional, TypeVar
from collections import OrderedDict
from rest_framework.response import Response as DRFResponse
from rest_framework import status as http_status

# ─── 泛型类型变量 ────────────────────────────────────────────
T = TypeVar("T")
DataT = TypeVar("DataT")


@dataclass(frozen=True)
class ApiResponse(Generic[T]):
    """
    统一 API 响应数据类（不可变）。

    知识点:
      - Generic[T]: 泛型，允许调用时指定 data 的类型
      - frozen=True: 不可变，类似 Java 的 record
      - field(default_factory=...): 为每个实例生成独立的默认值
    """
    code: int = 200
    message: str = "success"
    data: Optional[T] = None
    errors: Optional[list[dict[str, Any]]] = None

    def to_dict(self) -> OrderedDict:
        """
        转换为有序字典（保持字段顺序）。

        知识点:
          - 手动构建 dict 代替 asdict()，避免 MRO 冲突
          - 递归清洗：处理嵌套的 DRF ReturnDict / ReturnList
        """
        def _clean(val):
            # DRF ReturnList → list (必须放在 hasattr 前面，因为 ReturnList 也有 serializer)
            if isinstance(val, (list, tuple)):
                return [_clean(v) for v in val]
            # DRF ReturnDict → dict
            if hasattr(val, 'serializer'):
                return {k: _clean(v) for k, v in val.items()}
            if isinstance(val, dict):
                return {k: _clean(v) for k, v in val.items()}
            return val

        result = OrderedDict()
        for field_name in ('code', 'message', 'data', 'errors'):
            val = getattr(self, field_name, None)
            if val is not None:
                result[field_name] = _clean(val)
        return result

    def to_response(self, http_status_code: Optional[int] = None) -> DRFResponse:
        """
        转换为 DRF Response。

        知识点:
          - 默认参数为 None 时使用内部 code
          - DRF Response 接受 dict + http status
        """
        return DRFResponse(
            self.to_dict(),
            status=http_status_code or self.code,
        )

    # ─── 工厂类方法 ──────────────────────────────────────────
    # 知识点: @classmethod 不依赖实例，类似 Java 的 static factory

    @classmethod
    def success(
        cls,
        data: Any = None,
        message: str = "success",
    ) -> "ApiResponse":
        """操作成功。"""
        return cls(code=200, message=message, data=data)

    @classmethod
    def created(
        cls,
        data: Any = None,
        message: str = "创建成功",
    ) -> "ApiResponse":
        """资源创建成功。"""
        return cls(code=201, message=message, data=data)

    @classmethod
    def no_content(cls, message: str = "操作成功") -> "ApiResponse":
        """无返回内容的成功（如删除）。"""
        return cls(code=204, message=message)

    @classmethod
    def bad_request(
        cls,
        message: str = "请求参数错误",
        errors: Optional[list[dict[str, Any]]] = None,
    ) -> "ApiResponse":
        """请求参数错误。"""
        return cls(code=400, message=message, errors=errors)

    @classmethod
    def unauthorized(cls, message: str = "未登录或 Token 已过期") -> "ApiResponse":
        """未认证。"""
        return cls(code=401, message=message)

    @classmethod
    def forbidden(cls, message: str = "无权限访问") -> "ApiResponse":
        """无权限。"""
        return cls(code=403, message=message)

    @classmethod
    def not_found(cls, message: str = "资源不存在") -> "ApiResponse":
        """资源不存在。"""
        return cls(code=404, message=message)

    @classmethod
    def conflict(cls, message: str = "资源冲突") -> "ApiResponse":
        """资源冲突（如重复创建）。"""
        return cls(code=409, message=message)

    @classmethod
    def too_many_requests(cls, message: str = "请求过于频繁") -> "ApiResponse":
        """请求频率限制。"""
        return cls(code=429, message=message)

    @classmethod
    def server_error(cls, message: str = "服务器内部错误") -> "ApiResponse":
        """服务器内部错误。"""
        return cls(code=500, message=message)


# ─── 适配 DRF 的 Response 快捷函数 ───────────────────────────
def ok(data: Any = None, message: str = "success") -> DRFResponse:
    return ApiResponse.success(data, message).to_response()


def created(data: Any = None, message: str = "创建成功") -> DRFResponse:
    return ApiResponse.created(data, message).to_response(http_status.HTTP_201_CREATED)


def fail(
    message: str = "请求失败",
    code: int = 400,
    errors: Optional[list[dict]] = None,
) -> DRFResponse:
    return ApiResponse(code=code, message=message, errors=errors).to_response()
