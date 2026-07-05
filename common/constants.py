"""
全局常量定义。

知识点:
  - Python 没有真正的常量，全大写是约定（PEP 8）
  - `typing.Final` (Python 3.8+) 类型层面标记不可重赋值
  - typing 模块的各种类型标注
"""
from typing import Final

# ─── 分页 ────────────────────────────────────────────────────
DEFAULT_PAGE_SIZE: Final[int] = 20
MAX_PAGE_SIZE: Final[int] = 100

# ─── 缓存键前缀 ──────────────────────────────────────────────
CACHE_KEY_USER_PERMISSIONS: Final[str] = "user_permissions:{}"
CACHE_KEY_USER_MENU: Final[str] = "user_menu:{}"
CACHE_KEY_ARTICLE: Final[str] = "article:{}"
CACHE_KEY_DASHBOARD: Final[str] = "dashboard:{}"

# ─── 文件上传 ────────────────────────────────────────────────
ALLOWED_IMAGE_EXTENSIONS: Final[tuple[str, ...]] = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"
)
ALLOWED_DOCUMENT_EXTENSIONS: Final[tuple[str, ...]] = (
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt"
)
MAX_FILE_SIZE_MB: Final[int] = 50

# ─── 订单 ────────────────────────────────────────────────────
ORDER_EXPIRE_MINUTES: Final[int] = 30

# ─── 日志 ────────────────────────────────────────────────────
ACTION_CREATE: Final[str] = "CREATE"
ACTION_UPDATE: Final[str] = "UPDATE"
ACTION_DELETE: Final[str] = "DELETE"
ACTION_READ: Final[str] = "READ"
ACTION_EXPORT: Final[str] = "EXPORT"
ACTION_LOGIN: Final[str] = "LOGIN"
ACTION_LOGOUT: Final[str] = "LOGOUT"
