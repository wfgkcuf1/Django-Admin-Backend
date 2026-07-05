"""
生产环境配置 — 继承 base.py，强化安全与性能。

知识点:
  - `__all__` 限制通配符导入内容
  - import * 后选择性覆盖
  - 安全相关的 Python 最佳实践
"""
from .base import *  # noqa: F401, F403

# ─── 生产环境必须关闭调试 ─────────────────────────────────────
DEBUG = False

# ─── 强制 HTTPS ──────────────────────────────────────────────
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ─── 安全头 ──────────────────────────────────────────────────
SECURE_HSTS_SECONDS = 31536000  # 1 年
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# ─── 数据库连接池调优 ─────────────────────────────────────────
DATABASES["default"]["OPTIONS"] = {
    "pool_size": 20,
    "max_overflow": 40,
    "pool_timeout": 30,
    "pool_pre_ping": True,  # 连接前检测，防止断线
}

# ─── 缓存调优 ────────────────────────────────────────────────
CACHES["default"]["TIMEOUT"] = 600

# ─── Celery ──────────────────────────────────────────────────
CELERY_WORKER_CONCURRENCY = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 200
CELERY_WORKER_SEND_TASK_EVENTS = True
CELERY_TASK_SOFT_TIME_LIMIT = 600  # 10 分钟软限制

# ─── 日志 ────────────────────────────────────────────────────
LOGGING["handlers"]["file"]["level"] = "WARNING"
LOGGING["loggers"]["django"]["level"] = "WARNING"
LOGGING["loggers"]["apps"]["level"] = "INFO"
