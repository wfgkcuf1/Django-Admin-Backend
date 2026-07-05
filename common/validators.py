"""
自定义验证器 — 字段级别的校验函数。

知识点:
  1. 验证器是可调用对象（函数或类）
  2. `from django.core.exceptions import ValidationError`
  3. `__call__` 实现类验证器
  4. `re` 正则表达式
  5. `decorator` 模式: 验证器也支持组合
"""
import re
from typing import Any

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


# ─── 函数验证器 ──────────────────────────────────────────────
# 知识点: 验证器是普通的可调用函数
def validate_phone(value: str) -> None:
    """
    手机号验证器。

    知识点:
      - re.match: 匹配开头
      - ^ ... $: 完全匹配
      - raise ValidationError: 抛出验证错误
    """
    if not re.match(r"^1[3-9]\d{9}$", value):
        raise ValidationError(f"{value} 不是有效的手机号")


def validate_id_card(value: str) -> None:
    """身份证号简单验证。"""
    if not re.match(r"^\d{17}[\dXx]$", value):
        raise ValidationError(f"{value} 不是有效的身份证号")


# ─── 类验证器 ────────────────────────────────────────────────
# 知识点: @deconstructible 使得验证器可被 Django 迁移系统序列化
@deconstructible
class FileExtensionValidator:
    """
    文件扩展名验证器（类实现）。

    知识点:
      - __call__: 使类的实例可调用
      - 支持操作符: in, lower()
      - Path.suffix: 获取文件扩展名
    """

    def __init__(self, allowed_extensions: list[str]) -> None:
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions]

    def __call__(self, value: Any) -> None:
        """
        知识点:
          - 鸭子类型: 只要 value.name 存在即可
          - Path(value.name).suffix: 提取扩展名
        """
        from pathlib import Path

        ext = Path(value.name).suffix.lower() if hasattr(value, "name") else ""
        if ext and ext not in self.allowed_extensions:
            raise ValidationError(
                f"不支持的文件类型 {ext}，允许: {', '.join(self.allowed_extensions)}"
            )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FileExtensionValidator):
            return self.allowed_extensions == other.allowed_extensions
        return False


@deconstructible
class MaxFileSizeValidator:
    """
    文件大小验证器（类实现）。

    知识点:
      - size 属性: 文件大小
      - 单位换算: MB → bytes
    """

    def __init__(self, max_size_mb: int = 10) -> None:
        self.max_size_bytes = max_size_mb * 1024 * 1024

    def __call__(self, value: Any) -> None:
        if hasattr(value, "size") and value.size > self.max_size_bytes:
            max_mb = self.max_size_bytes / 1024 / 1024
            raise ValidationError(f"文件大小不能超过 {max_mb:.0f}MB")

    def __eq__(self, other: object) -> bool:
        if isinstance(other, MaxFileSizeValidator):
            return self.max_size_bytes == other.max_size_bytes
        return False


# ─── 组合验证器 ──────────────────────────────────────────────
def compose_validators(*validators) -> callable:
    """
    组合多个验证器为一个。

    知识点:
      - 高阶函数: 接收验证器列表，返回新验证器
      - 列表推导式: 逐个执行验证器
      - *args, **kwargs 透传

    用法:
      validate_image = compose_validators(
          FileExtensionValidator([".jpg", ".png"]),
          MaxFileSizeValidator(5),
      )
    """
    def composed(value: Any) -> None:
        for validator in validators:
            validator(value)

    return composed
