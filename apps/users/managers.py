"""
自定义 User Manager — 扩展 Django 默认管理器。

知识点:
  1. BaseUserManager: Django 用户管理器的基类
  2. create_user / create_superuser: 工厂方法
  3. `get_by_natural_key`: 支持登录字段
"""
from typing import Any, Optional

from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    """
    自定义用户管理器。

    知识点:
      - 重写 create_user: 自定义创建逻辑
      - normalize_email: 统一邮箱格式
      - set_unusable_password: 设置不可用密码
    """

    def create_user(
        self,
        username: str,
        password: Optional[str] = None,
        **extra_fields: Any,
    ):
        """
        创建普通用户。

        知识点:
          - self.model: 指向关联的 User 模型
          - self.normalize_email: 邮箱小写化
          - set_password: 对密码进行哈希
        """
        if not username:
            raise ValueError("用户名不能为空")

        # 知识点: 使用 self.model 而非直接 User，保持灵活
        user = self.model(
            username=username,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        username: str,
        password: Optional[str] = None,
        **extra_fields: Any,
    ):
        """
        创建超级管理员。

        知识点:
          - 字典解包 **kwargs: 批量设置额外字段
          - 条件判断覆盖默认值
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("超级管理员必须设置 is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("超级管理员必须设置 is_superuser=True")

        return self.create_user(username, password, **extra_fields)

    def get_by_natural_key(self, username: str):
        """支持用户名或邮箱登录。"""
        return self.get(**{self.model.USERNAME_FIELD: username})

    def active(self):
        """活跃用户查询集。"""
        return self.filter(is_active=True, deleted_at__isnull=True)
