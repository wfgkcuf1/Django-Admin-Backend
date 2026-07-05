"""
枚举定义 — 使用 Python `enum` 模块替代散落的魔法字符串。

知识点:
  1. `enum.Enum` — 基础枚举
  2. `enum.IntEnum` — 值是整数的枚举（可作数据库字段）
  3. `enum.StrEnum` — 值是字符串的枚举（Python 3.11+）
  4. `@unique` — 装饰器，强制值唯一
  5. `auto()` — 自动赋值（从 1 开始递增）
  6. 枚举方法 — 枚举也可以有方法
  7. `__iter__` / `__contains__` — 自定义枚举行为
"""
from enum import Enum, IntEnum, StrEnum, auto, unique


class Status(IntEnum):
    """通用启用/禁用状态。"""
    DISABLED = 0
    ENABLED = 1

    @classmethod
    def choices(cls) -> list[tuple[int, str]]:
        """Django 模型字段 compatible choices。"""
        return [(m.value, m.name) for m in cls]


@unique
class UserRole(StrEnum):
    """用户角色 — @unique 保证值唯一。"""
    ADMIN = "admin"          # 超级管理员
    MANAGER = "manager"      # 管理员
    EDITOR = "editor"        # 编辑
    USER = "user"            # 普通用户
    GUEST = "guest"          # 访客

    @property
    def label(self) -> str:
        """枚举属性 — 返回中文标签。"""
        labels = {
            "admin": "超级管理员",
            "manager": "管理员",
            "editor": "编辑",
            "user": "普通用户",
            "guest": "访客",
        }
        return labels[self.value]

    @classmethod
    def admin_levels(cls) -> set["UserRole"]:
        """返回所有管理级别角色。"""
        return {cls.ADMIN, cls.MANAGER}


class Gender(IntEnum):
    """性别。"""
    UNKNOWN = 0
    MALE = 1
    FEMALE = 2

    @classmethod
    def choices(cls) -> list[tuple[int, str]]:
        return [(m.value, m.name) for m in cls]


class OrderStatus(StrEnum):
    """订单状态。"""
    PENDING = "pending"          # 待处理
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成
    CANCELLED = "cancelled"      # 已取消
    REFUNDED = "refunded"        # 已退款

    @property
    def is_terminal(self) -> bool:
        """是否是终态（不可再变更）。"""
        return self in (self.COMPLETED, self.CANCELLED, self.REFUNDED)


class ArticleStatus(StrEnum):
    """文章状态。"""
    DRAFT = "draft"              # 草稿
    PENDING_REVIEW = "pending"   # 待审核
    PUBLISHED = "published"      # 已发布
    REJECTED = "rejected"        # 已驳回
    ARCHIVED = "archived"        # 已归档

    @classmethod
    def publishable(cls) -> set["ArticleStatus"]:
        """可以手动发布的几种状态。"""
        return {cls.DRAFT, cls.REJECTED}


class FileType(StrEnum):
    """文件类型分类。"""
    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"
    OTHER = "other"


class LogLevel(StrEnum):
    """日志级别。"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class NotificationType(StrEnum):
    """通知类型。"""
    SYSTEM = "system"
    ORDER = "order"
    APPROVAL = "approval"
    MESSAGE = "message"
