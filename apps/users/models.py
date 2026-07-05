"""
用户模型 — 自定义 Django User。

知识点:
  1. AbstractBaseUser: 只包含认证字段（password, last_login）
  2. PermissionsMixin: 添加权限字段（is_superuser, groups, user_permissions）
  3. AbstractUser: 包含上面两者 + 默认字段（username, email, first_name 等）
  4. 我们选择 AbstractUser 并扩展（比完全自建更省事）
  5. USERNAME_FIELD: 登录用的字段
  6. REQUIRED_FIELDS: createsuperuser 时提示的必填字段
  7. objects: 自定义管理器
  8. `@property` 计算字段
  9. `__str__` 字符串表示
"""
from datetime import datetime

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from common.enums import Gender, UserRole, Status
from common.base_model import BaseModel
from .managers import UserManager


class User(AbstractUser):
    """
    自定义用户模型 — 扩展 Django 内置 User。

    知识点:
      - 继承 AbstractUser 而非 AbstractBaseUser:
        AbstractUser = AbstractBaseUser + PermissionsMixin + 默认字段
      - 重写字段类型以匹配业务需求
      - 添加自定义字段
      - unique=True: 唯一约束
      - choices: 枚举约束
    """

    # ─── 覆盖默认字段 ──────────────────────────────────────
    # username 默认是 150 字符，保持但加索引
    username = models.CharField(
        verbose_name="用户名",
        max_length=150,
        unique=True,
        db_index=True,
        help_text="登录使用的用户名",
    )

    email = models.EmailField(
        verbose_name="邮箱",
        unique=True,
        null=True,
        blank=True,
        db_index=True,
    )

    phone = models.CharField(
        verbose_name="手机号",
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
    )

    # ─── 自定义字段 ────────────────────────────────────────
    # 知识点: CharField + choices = 字符串枚举（数据库存字符串）
    role = models.CharField(
        verbose_name="角色",
        max_length=20,
        choices=[(r.value, r.label) for r in UserRole],
        default=UserRole.USER.value,
        db_index=True,
    )

    # 知识点: IntegerField + choices = 整数枚举（存整数，更高效）
    gender = models.IntegerField(
        verbose_name="性别",
        choices=Gender.choices(),
        default=Gender.UNKNOWN.value,
    )

    avatar = models.URLField(
        verbose_name="头像 URL",
        max_length=500,
        blank=True,
        default="",
    )

    nickname = models.CharField(
        verbose_name="昵称",
        max_length=50,
        blank=True,
        default="",
    )

    # ─── 用户状态字段（扩展） ───────────────────────────────
    # 知识点: DateTimeField 记录最后活跃时间
    last_active_at = models.DateTimeField(
        verbose_name="最后活跃时间",
        null=True,
        blank=True,
    )

    # 软删除
    deleted_at = models.DateTimeField(
        verbose_name="删除时间",
        null=True,
        blank=True,
        db_index=True,
    )

    # ─── 关联 ─────────────────────────────────────────────
    # created_by 自关联（记录谁创建了这个用户）
    created_by = models.ForeignKey(
        "self",
        verbose_name="创建人",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_users",
    )

    # ─── 配置 ─────────────────────────────────────────────
    # 知识点: 使用自定义管理器
    objects = UserManager()

    # 登录字段（Django 3.x+ 支持 email 或 username）
    USERNAME_FIELD = "username"

    # 创建超级用户时的必填提示字段（非数据库约束）
    REQUIRED_FIELDS = ["email"]

    class Meta(AbstractUser.Meta):
        db_table = "sys_user"
        verbose_name = "用户"
        verbose_name_plural = "用户列表"
        ordering = ["-date_joined"]
        # 知识点: 复合索引
        indexes = [
            models.Index(fields=["role", "is_active"]),
            models.Index(fields=["deleted_at", "is_active"]),
        ]

    def __str__(self) -> str:
        """字符串表示。"""
        return self.username or self.phone or str(self.pk)

    def __repr__(self) -> str:
        return f"<User {self.username}({self.pk}) role={self.role}>"

    # ─── 属性 ─────────────────────────────────────────────
    @property
    def is_admin(self) -> bool:
        """是否是超级管理员。"""
        return self.is_superuser or self.role == UserRole.ADMIN.value

    @property
    def is_manager(self) -> bool:
        """是否是管理员/超级管理员。"""
        return self.is_admin or self.role == UserRole.MANAGER.value

    @property
    def display_name(self) -> str:
        """显示名称（nickname > username > phone）。"""
        return self.nickname or self.username or self.phone or "未知用户"

    @property
    def role_label(self) -> str:
        """角色的中文标签。"""
        try:
            return UserRole(self.role).label
        except ValueError:
            return self.role

    @property
    def age(self) -> int:
        """计算年龄（基于 date_joined 近似）。"""
        # 知识点: 不是真实年龄，演示 @property 计算逻辑
        if self.date_joined:
            delta = timezone.now() - self.date_joined
            return delta.days // 365
        return 0

    # ─── 方法 ─────────────────────────────────────────────
    def update_last_active(self) -> None:
        """更新最后活跃时间。"""
        User.objects.filter(pk=self.pk).update(
            last_active_at=timezone.now()
        )
        self.last_active_at = timezone.now()

    def soft_delete(self) -> None:
        """软删除用户。"""
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=["deleted_at", "is_active"])

    def restore(self) -> None:
        """恢复已删除用户。"""
        self.deleted_at = None
        self.is_active = True
        self.save(update_fields=["deleted_at", "is_active"])

    def has_role(self, *roles: str) -> bool:
        """
        检查用户是否拥有指定角色之一。

        知识点:
          - *args: 可变参数
          - any(): 任意一个匹配即 True
        """
        return any(self.role == role for role in roles)
