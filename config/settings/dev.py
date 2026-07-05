"""
开发环境配置 — 继承 base.py 并覆盖调试设置。

知识点:
  - Python 模块导入: `from .base import *` 相对导入
  - `__all__` 控制 `from module import *` 导出的符号
  - 通过 `hasattr` 做安全覆盖检查
"""
from .base import *  # noqa: F401, F403 — 导入所有 base 配置

# ─── 明确关闭生产安全特性 ─────────────────────────────────────
DEBUG = True

# 开发环境允许所有 Host
ALLOWED_HOSTS = ["*"]

# ─── 打印 SQL 到控制台 ──────────────────────────────────────
# 知识点: hasattr 安全判断 + 列表追加
if hasattr(locals(), "LOGGING"):
    LOGGING["loggers"]["django.db.backends"] = {
        "handlers": ["console"],
        "level": "WARNING",  # 改成 DEBUG 可以看到每条 SQL
        "propagate": False,
    }

# ─── 开发环境的数据库 ─────────────────────────────────────────
# 知识点: vars() / locals() 检查变量是否存在
# 开发环境用 SQLite 兜底，方便没有 PostgreSQL 的同学
if get_env("USE_SQLITE", "false").lower() in ("true", "1"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ─── CORS 开发环境宽放 ───────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True

# ─── 缓存：开发环境用本地内存（不需要 Redis）────────────────
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "dev-cache",
    }
}

# ─── drf-spectacular 开发环境开放 ────────────────────────────
SPECTACULAR_SETTINGS["SERVE_PUBLIC"] = True
