"""
用户视图 — 登录/注册 + 用户 CRUD。

知识点:
  1. ModelViewSet: CRUD 一站式视图
  2. @action: 自定义路由（detail / detail=False）
  3. APIView: 原始视图基类（非 CRUD 场景）
  4. 权限控制: 不同 action 不同权限
  5. ViewSetMixin + APIView 混合
"""
import logging
from typing import Any, Optional

from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets, generics
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from common.base_view import BaseViewSet
from common.exceptions import BusinessError, ResourceNotFound
from common.response import ApiResponse, ok, created, fail
from common.enums import UserRole
from common.pagination import StandardPagination
from .filters import UserFilter
from .models import User
from .serializers import (
    UserListSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserPasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
)
from .permissions import IsSelfOrAdmin, AdminOnlyUserManagement

logger = logging.getLogger(__name__)


# ─── 认证视图（APIView） ─────────────────────────────────────
class LoginView(generics.GenericAPIView):
    """
    登录接口。

    知识点:
      - GenericAPIView: 比 APIView 多了一些序列化器相关功能
      - 不继承 ViewSet，因为不需要 CRUD
      - permission_classes = [AllowAny]: 任何人都可以访问
    """

    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    authentication_classes = []  # 登录接口不需要认证

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """用户登录。"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # 知识点: RefreshToken.for_user() 生成 JWT
        refresh = RefreshToken.for_user(user)

        # 知识点: 更新最后登录时间
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        # 知识点: dict(serializer.data) 将 DRF 的 ReturnDict 转纯 dict
        return ApiResponse.success(
            data={
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": dict(UserListSerializer(user).data),
            },
            message="登录成功",
        ).to_response()


class RegisterView(generics.CreateAPIView):
    """
    注册接口。

    知识点:
      - CreateAPIView: 只提供 POST 的视图
      - queryset: 指定查询集（用于唯一性验证）
      - 注册成功后自动登录（返回 JWT）
    """

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """注册并返回 JWT。"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # 知识点: 注册后自动生成 Token
        refresh = RefreshToken.for_user(user)

        return ApiResponse.created(
            data={
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": dict(UserListSerializer(user).data),
            },
            message="注册成功",
        ).to_response()


class TokenRefreshView(generics.GenericAPIView):
    """
    Token 刷新接口（如果需要自定义刷新逻辑）。

    知识点:
      - rest_framework_simplejwt.views.TokenRefreshView 已经够用了
      - 这里只做展示，实际使用 simplejwt 自带的
    """

    pass


# ─── 用户 CRUD 视图集 ───────────────────────────────────────
class UserViewSet(BaseViewSet):
    """
    用户管理视图集。

    知识点:
      - 不同 action 使用不同的 serializer
      - get_permissions(): 动态权限
      - get_serializer_class(): 动态序列化器
    """

    queryset = User.objects.active()  # 自定义管理器方法
    serializer_class = UserListSerializer
    filterset_class = UserFilter
    search_fields = ["username", "email", "phone", "nickname"]
    ordering_fields = ["date_joined", "last_login", "username"]
    ordering = "-date_joined"
    pagination_class = StandardPagination

    # ─── 权限映射 ──────────────────────────────────────────
    def get_permissions(self):
        """
        不同操作不同权限。

        知识点:
          - 动态权限: 根据 action 返回不同的权限列表
          - DRF 权限检查机制
        """
        if self.action == "create":
            return [AllowAny()]  # 任何人都可以注册
        elif self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsSelfOrAdmin()]
        elif self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        """
        动态选择序列化器。

        知识点:
          - 不同 action 用不同序列化器
          - 覆盖默认的 get_serializer_class()
        """
        if self.action == "create":
            return UserCreateSerializer
        elif self.action in ("update", "partial_update"):
            return UserUpdateSerializer
        elif self.action == "retrieve":
            return UserDetailSerializer
        return UserListSerializer

    def get_queryset(self):
        """
        根据用户角色限制可见范围。

        知识点:
          - 超级管理员: 看到所有用户（含软删除）
          - 普通管理员: 看到非软删除
          - 普通用户: 只能看到自己
        """
        user = self.request.user

        # 知识点: 超级管理员可以看到所有（含已删除）
        if user.is_superuser:
            return User.objects.all()

        # 管理员可以看到活跃用户
        if user.is_staff:
            return User.objects.active()

        # 普通用户只能看到自己
        return User.objects.filter(pk=user.pk)

    # ─── 自定义操作 ─────────────────────────────────────────
    @action(detail=True, methods=["post"])
    def reset_password(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        管理员重置用户密码（不需要旧密码）。

        知识点:
          - @action(detail=True): 作用于单个资源
          - request.data 获取请求体
          - set_password 哈希密码
        """
        user = self.get_object()
        new_password = request.data.get("new_password")

        if not new_password or len(new_password) < 6:
            return fail(message="密码至少 6 位")

        user.set_password(new_password)
        user.save(update_fields=["password"])

        logger.info(f"管理员 {request.user} 重置了用户 {user} 的密码")
        return ok(message="密码重置成功")

    @action(detail=True, methods=["post"])
    def toggle_active(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        切换用户启用/禁用状态。

        知识点:
          - post 操作可以修改资源状态
          - 不能禁用自己
        """
        user = self.get_object()
        if user.pk == request.user.pk:
            return fail(message="不能禁用自己")

        # 知识点: 三元表达式切换 boolean
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])

        status_text = "启用" if user.is_active else "禁用"
        logger.info(f"用户 {user.username} 已被 {status_text}")
        return ok(data={"is_active": user.is_active}, message=f"已{status_text}")

    @action(detail=True, methods=["post"])
    def soft_delete(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        软删除用户。

        知识点:
          - 使用模型方法
        """
        user = self.get_object()
        if user.is_superuser:
            return fail(message="不能删除超级管理员")

        user.soft_delete()
        logger.info(f"用户 {user.username} 已被软删除")
        return ok(message="用户已删除")

    @action(detail=True, methods=["post"])
    def restore(self, request: Request, pk: Optional[str] = None) -> Response:
        """恢复已删除用户。"""
        user = User.objects.get(pk=pk)
        user.restore()
        logger.info(f"用户 {user.username} 已恢复")
        return ok(message="用户已恢复")

    @action(detail=False, methods=["get"])
    def me(self, request: Request) -> Response:
        """
        获取当前登录用户信息。

        知识点:
          - @action(detail=False): 作用于列表（不依赖 pk）
          - request.user: 当前认证用户
        """
        serializer = UserDetailSerializer(request.user)
        # 知识点: dict() 将 DRF ReturnDict 转纯 dict
        return ok(data=dict(serializer.data))

    @action(detail=False, methods=["patch"])
    def update_me(self, request: Request) -> Response:
        """
        更新当前用户信息。

        知识点:
          - partial=True: 部分更新
        """
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ok(data=serializer.data, message="个人信息已更新")

    @action(detail=False, methods=["post"])
    def change_password(self, request: Request) -> Response:
        """
        当前用户修改密码。

        知识点:
          - Serializer 验证旧密码
          - set_password 设置新密码
        """
        serializer = UserPasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])

        return ok(message="密码修改成功")
