"""
基础模型层 — 所有模型的基类。

知识点:
  1. 抽象模型 `class Meta: abstract = True`
  2. Mixin 类 — 多继承组合行为
  3. `__str__` 魔法方法
  4. `@classmethod` — 类方法（类似 Java static method 但可继承）
  5. `@staticmethod` — 静态方法（工具函数）
  6. `@property` — 计算字段（属性装饰器）
  7. `save()` / `delete()` 重写 — 自带钩子
  8. `update()` 批量更新方法
  9. `datetime` / `timezone` 时间处理
  10. `uuid` — 分布式 ID
"""
import uuid
import logging
from datetime import datetime
from typing import Any, Optional

from django.db import models
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)


class TimestampMixin(models.Model):
    """
    时间戳混入类 — 自动记录创建和更新时间。

    知识点:
      - abstract=True: 不创建数据库表，只作为基类
      - auto_now_add: 创建时自动记录（不可修改）
      - auto_now: 每次保存自动更新
    """
    created_at = models.DateTimeField(
        verbose_name="创建时间",
        auto_now_add=True,
        db_index=True,
    )
    updated_at = models.DateTimeField(
        verbose_name="更新时间",
        auto_now=True,
    )

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """
    软删除混入类 — 逻辑删除而非物理删除。

    知识点:
      - deleted_at 为 NULL 表示未删除
      - 自定义 objects + deleted_objects 管理器
      - objects.filter(deleted_at__isnull=True): 默认只查未删除
    """
    deleted_at = models.DateTimeField(
        verbose_name="删除时间",
        null=True,
        blank=True,
        db_index=True,
    )

    class Meta:
        abstract = True

    def soft_delete(self) -> None:
        """软删除：设置删除时间。"""
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])
        logger.info(f"{self.__class__.__name__}({self.pk}) 已软删除")

    def restore(self) -> None:
        """恢复软删除。"""
        self.deleted_at = None
        self.save(update_fields=["deleted_at", "updated_at"])
        logger.info(f"{self.__class__.__name__}({self.pk}) 已恢复")

    @property
    def is_deleted(self) -> bool:
        """是否已删除。"""
        return self.deleted_at is not None


class UUIDPrimaryKeyMixin(models.Model):
    """
    UUID 主键混入类 — 替代自增整数主键。

    知识点:
      - uuid.uuid4(): 生成随机 UUID（v4）
      - default=uuid.uuid4: 模型层面设默认值（可读性好）
      - editable=False: 管理后台不可编辑
      - primary_key=True: 设为主键
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )

    class Meta:
        abstract = True


class OperatorStampedMixin(models.Model):
    """
    操作人记录混入类 — 记录创建/更新操作人。

    知识点:
      - ForeignKey: 外键关联
      - null=True: 允许为空（如系统自动创建）
      - on_delete=models.SET_NULL: 用户删除时不级联删除
      - related_name: 反向关联名（避免冲突）
    """
    created_by = models.ForeignKey(
        "users.User",
        verbose_name="创建人",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
    )
    updated_by = models.ForeignKey(
        "users.User",
        verbose_name="更新人",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated",
    )

    class Meta:
        abstract = True


class BaseModel(TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin, OperatorStampedMixin):
    """
    完整基础模型 — 组合所有混入类。

    知识点:
      - 多继承: MRO (Method Resolution Order) 决定方法查找顺序
      - class Meta 配置: ordering, verbose_name
      - @classmethod 批量更新
    """
    is_active = models.BooleanField(
        verbose_name="是否启用",
        default=True,
        db_index=True,
    )
    remark = models.TextField(
        verbose_name="备注",
        blank=True,
        default="",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """
        对象的字符串表示 — 用于 admin、日志等地方。

        知识点:
          - __str__: 面向用户的字符串
          - __repr__: 面向开发者的字符串（for debugging）
        """
        return f"{self.__class__.__name__}({self.pk})"

    def __repr__(self) -> str:
        """更详细的调试表示。"""
        return (
            f"<{self.__class__.__name__} "
            f"id={self.pk} "
            f"created_at={self.created_at.isoformat() if hasattr(self, 'created_at') else 'N/A'}>"
        )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        重写 save — 自动清除更新时的缓存。

        知识点:
          - super(): 调用父类方法
          - *args, **kwargs: 透传所有参数
          - cache.delete: 自动清除关联缓存
        """
        # 清除该对象的缓存
        cache_key = f"model:{self.__class__.__name__}:{self.pk}"
        cache.delete(cache_key)

        return super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        """
        重写 delete — 自动清除缓存。
        """
        cache_key = f"model:{self.__class__.__name__}:{self.pk}"
        cache.delete(cache_key)
        return super().delete(*args, **kwargs)

    @classmethod
    def bulk_update_or_create(
        cls,
        defaults: dict[str, Any],
        **kwargs: Any,
    ) -> tuple[Any, bool]:
        """
        更新或创建（类方法，基于 kwargs 查找）。

        知识点:
          - @classmethod: 第一个参数是 cls 而非 self
          - cls.objects: 使用当前模型的 Manager
        """
        obj, created = cls.objects.update_or_create(
            defaults=defaults,
            **kwargs,
        )
        return obj, created

    def to_dict(self) -> dict[str, Any]:
        """
        将模型转换为 dict（用于序列化 / 缓存）。

        知识点:
          - 字典推导式
          - 使用 __dict__ 但过滤掉 Django 内部字段
          - isinstance / callable 类型检查
        """
        result = {}
        for field in self._meta.fields:
            name = field.attname
            value = getattr(self, name)
            # 处理 datetime 对象 → ISO 字符串
            if isinstance(value, datetime):
                value = value.isoformat()
            # 处理 UUID → 字符串
            elif isinstance(value, uuid.UUID):
                value = str(value)
            result[name] = value
        return result

    def refresh(self) -> None:
        """从数据库重新加载。"""
        return self.refresh_from_db()
