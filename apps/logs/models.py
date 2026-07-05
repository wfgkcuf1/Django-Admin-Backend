"""
操作日志模型 — 记录所有用户操作。

知识点:
  1. GenericForeignKey: 通用外键（关联任意模型）
  2. JSONField: 存储 JSON 结构数据
  3. IP 地址存储: GenericIPAddressField
"""
import uuid

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from common.base_model import TimestampMixin


class OperationLog(TimestampMixin):
    """操作日志。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "users.User",
        verbose_name="操作用户",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    username = models.CharField(verbose_name="用户名", max_length=150, blank=True, db_index=True)
    action = models.CharField(verbose_name="操作类型", max_length=20, db_index=True)
    model_name = models.CharField(verbose_name="操作模型", max_length=100, blank=True)
    object_id = models.CharField(verbose_name="对象 ID", max_length=100, blank=True)
    detail = models.TextField(verbose_name="操作详情", blank=True)
    changes = models.JSONField(verbose_name="变更内容", null=True, blank=True)
    ip_address = models.GenericIPAddressField(verbose_name="IP 地址", blank=True, null=True)
    user_agent = models.TextField(verbose_name="用户代理", blank=True)
    duration_ms = models.IntegerField(verbose_name="耗时(ms)", default=0)
    status = models.CharField(verbose_name="状态", max_length=10, default="success")

    class Meta:
        db_table = "sys_operation_log"
        verbose_name = "操作日志"
        verbose_name_plural = "操作日志"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
            models.Index(fields=["model_name", "object_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} {self.model_name}({self.object_id}) by {self.username}"
