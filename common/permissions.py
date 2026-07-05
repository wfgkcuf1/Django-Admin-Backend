"""
自定义权限系统 — 基于角色的访问控制 (RBAC)。

知识点:
  1. DRF 权限类: BasePermission → 自定义子类
  2. `has_permission`: 视图级权限检查
  3. `has_object_permission`: 对象级权限检查
  4. `@classmethod` + `@abstractmethod` 抽象权限定义
  5. 位运算: `&` (AND) / `|` (OR) 组合权限
"""
import logging
from typing import Any

from rest_framework.permissions import (
    BasePermission,
    SAFE_METHODS,
    IsAuthenticated,
    IsAdminUser,
    AllowAny,
)

logger = logging.getLogger(__name__)


class IsAuthenticatedOrReadOnlyCustom(BasePermission):
    """
    自定义 — 安全方法（GET/HEAD/OPTIONS）允许任意访问，
    写方法需要认证。

    知识点:
      - SAFE_METHODS: ("GET", "HEAD", "OPTIONS")
      - request.method in SAFE_METHODS
    """

    def has_permission(self, request, view) -> bool:
        # 知识点: 读操作不限制
        if request.method in SAFE_METHODS:
            return True
        # 写操作需要认证
        return request.user and request.user.is_authenticated


class IsSuperAdmin(BasePermission):
    """仅超级管理员。"""

    def has_permission(self, request, view) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )


class IsStaff(BasePermission):
    """仅管理员（含超级管理员）。"""

    def has_permission(self, request, view) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )


class IsOwner(BasePermission):
    """
    对象级权限 — 只能操作自己的资源。

    知识点:
      - has_object_permission: 在 get_object() 时触发
      - obj.user == request.user: 检查所有权
    """

    def has_object_permission(self, request, view, obj) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        # 知识点: getattr 安全获取 user 属性
        owner = getattr(obj, "user", None) or getattr(obj, "created_by", None)
        return owner == request.user


class RoleBasedPermission(BasePermission):
    """
    基于角色的权限 — 按 action 检查角色。

    使用:
      class ArticleViewSet(BaseViewSet):
          permission_classes = [
              RoleBasedPermission(
                  admin=["create", "update", "destroy"],
                  staff=["create", "update"],
                  user=["list", "retrieve"],
              )
          ]
    """

    def __init__(
        self,
        admin: list[str] | None = None,
        staff: list[str] | None = None,
        user: list[str] | None = None,
    ) -> None:
        self._role_actions = {
            "admin": set(admin or []),
            "staff": set(staff or []),
            "user": set(user or []),
        }

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        # 知识点: view.action 获取当前操作名（如 list, create）
        action = getattr(view, "action", "")

        # 超级管理员拥有所有权限
        if request.user.is_superuser:
            return True

        # 知识点: getattr 配合 safe defaults
        role = getattr(request.user, "role", "user")

        # 检查角色是否有此操作权限
        allowed_actions = self._role_actions.get(role, set())
        # 知识点: 通配符 * 表示所有操作
        if "*" in allowed_actions:
            return True

        return action in allowed_actions


class PermissionCacheMixin(BasePermission):
    """
    缓存感知权限 — 权限检查结果缓存到 Redis。

    知识点:
      - 用缓存加速频繁的权限检查
      - cache.get / cache.set 组合
    """

    CACHE_PREFIX = "perm_check:"
    CACHE_TTL = 60  # 60 秒

    def has_permission(self, request, view) -> bool:
        from django.core.cache import cache

        if not request.user or not request.user.is_authenticated:
            return False

        # 知识点: 生成缓存键
        cache_key = f"{self.CACHE_PREFIX}{request.user.id}:{view.__class__.__name__}"

        # 尝试从缓存获取
        if (result := cache.get(cache_key)) is not None:
            return result

        # 执行实际检查（由子类实现）
        result = self._check_permission(request, view)

        # 缓存结果
        cache.set(cache_key, result, self.CACHE_TTL)

        return result

    def _check_permission(self, request, view) -> bool:
        """子类实现具体检查逻辑。"""
        return True
