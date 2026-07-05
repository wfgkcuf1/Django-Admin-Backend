"""
基础序列化器 — 所有序列化器的基类。

知识点:
  1. `Serializer` vs `ModelSerializer`
  2. `validated_data`: 验证后的干净数据
  3. `create()` / `update()` 重写
  4. `validate_<field>` 字段级验证
  5. `validate()` 对象级验证
  6. `to_representation()` / `to_internal_value()` 数据转换
  7. `Meta.fields = "__all__"` 快捷方式
  8. 嵌套序列化器
"""
import logging
from typing import Any, Optional

from django.db import transaction
from rest_framework import serializers

logger = logging.getLogger(__name__)


class BaseModelSerializer(serializers.ModelSerializer):
    """
    基础模型序列化器 — 所有 ModelSerializer 的基类。

    知识点:
      - 重写 create/update 添加操作人
      - 自动注入 request.user 到 created_by / updated_by
    """

    # ─── 通用字段 ──────────────────────────────────────────
    # 知识点: ReadOnlyField 仅在序列化输出时包含，不接受输入
    id = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")
    updated_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")

    def create(self, validated_data: dict[str, Any]) -> Any:
        """
        创建 — 自动注入当前用户为 created_by。

        知识点:
          - self.context.get("request"): 从视图上下文获取请求
          - request.user: 当前认证用户
          - 注入额外字段到 validated_data
        """
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            # 知识点: setdefault 只在键不存在时设置值
            validated_data.setdefault("created_by", request.user)
            validated_data.setdefault("updated_by", request.user)

        return super().create(validated_data)

    def update(self, instance: Any, validated_data: dict[str, Any]) -> Any:
        """
        更新 — 自动更新 updated_by。

        知识点:
          - 部分更新时只更新提供的字段
          - 使用 super() 调用父类方法
        """
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            validated_data["updated_by"] = request.user

        return super().update(instance, validated_data)


class TreeSerializer(serializers.Serializer):
    """
    树形结构序列化器 — 递归序列化树形数据。

    知识点:
      - `Serializer` 不是 `ModelSerializer`，手动定义字段
      - 递归字段: `serializers.SerializerMethodField`
      - @transaction.atomic 事务装饰器
    """

    id = serializers.UUIDField()
    label = serializers.CharField()
    children = serializers.SerializerMethodField()

    def get_children(self, obj: Any) -> list[dict]:
        """
        递归获取子节点。

        知识点:
          - SerializerMethodField: 通过 get_<field> 方法计算值
          - 递归调用自身序列化子节点
        """
        if hasattr(obj, "get_children"):
            children = obj.get_children()
            if children:
                return TreeSerializer(children, many=True).data
        return []


class BulkSerializerMixin:
    """
    批量操作序列化器混入类。

    知识点:
      - Mixin + Serializer 组合
      - 列表输入验证
    """

    def validate_ids(self, ids: list[str]) -> list[str]:
        """验证 ID 列表。"""
        if not ids:
            raise serializers.ValidationError("ID 列表不能为空")
        if len(ids) > 1000:
            raise serializers.ValidationError("单次操作最多 1000 条")
        return ids
