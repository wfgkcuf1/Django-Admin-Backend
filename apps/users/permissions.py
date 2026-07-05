"""
用户模块权限 — 具体到用户管理的权限检查。

知识点:
  - 可组合的权限类
  - & 和 | 运算符组合权限
"""
from rest_framework.permissions import BasePermission


class IsSelfOrAdmin(BasePermission):
    """
    只能操作自己（或管理员可以操作任何人）。

    知识点:
      - has_object_permission: 对象级权限
      - superuser 跳过所有对象级检查
    """

    def has_object_permission(self, request, view, obj) -> bool:
        if request.user.is_superuser:
            return True
        return obj.pk == request.user.pk


class AdminOnlyUserManagement(BasePermission):
    """
    只有管理员可以管理用户（创建/更新/删除）。

    知识点:
      - has_permission 中检查视图 action
      - SAFE_METHODS 放行读操作
    """

    def has_permission(self, request, view) -> bool:
        # 读操作放行
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        # 写操作需要管理员
        return request.user.is_staff or request.user.is_superuser
