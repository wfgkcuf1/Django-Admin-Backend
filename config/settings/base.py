"""
Django 基础配置 — 所有环境共享的公共配置。

知识点（Python 层面）:
  1. `from pathlib import Path` — 面向对象路径操作，比 os.path 更现代
  2. `os.environ.get("KEY", default)` — 环境变量读取，可设默认值
  3. `@functools.lru_cache` — 函数结果缓存装饰器
  4. 列表/字典解包 `[*list1, *list2]`、`{**dict1, **dict2}`
  5. 海象运算符 `:=` — 赋值表达式（Python 3.8+）
"""
import os
from pathlib import Path
from datetime import timedelta
from functools import lru_cache

# ─── 项目路径 ────────────────────────────────────────────────
# Path(__file__).resolve() → 当前文件的绝对路径
# .parent → 父目录（settings/） → 再 parent → config/ → 再 parent → 项目根
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ─── 环境变量助手 ────────────────────────────────────────────
# 知识点: lru_cache 让多次调用只读一次文件
@lru_cache(maxsize=1)
def get_env(key: str, default: str = "") -> str:
    """
    获取环境变量，带缓存避免重复 I/O。

    知识点:
      - @lru_cache: 最近最少使用缓存，maxsize=1 表示只缓存最近 1 个结果
      - 但这里实际是每个 key 独立缓存，因为入参不同
      - dotenv 加载 .env 文件到 os.environ
    """
    # 首次调用时加载 .env 文件
    try:
        from dotenv import load_dotenv
        env_path = BASE_DIR / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    except ImportError:
        pass  # dotenv 未安装时静默跳过，生产环境用系统环境变量
    return os.environ.get(key, default)


# ─── 安全 ────────────────────────────────────────────────────
# 知识点: 海象运算符 `:=` — 在表达式内赋值
if (secret_key := get_env("DJANGO_SECRET_KEY")) and secret_key.startswith("django-insecure"):
    import warnings
    warnings.warn(
        f"⚠️  警告: 使用了不安全的默认 SECRET_KEY！"
        f" 请为生产环境设置强随机密钥。",
        RuntimeWarning,
        stacklevel=2,
    )

SECRET_KEY = get_env("DJANGO_SECRET_KEY", "django-insecure-fallback-key")

DEBUG = get_env("DJANGO_DEBUG", "False").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = get_env(
    "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1"
).split(",")

# ─── 应用注册 ────────────────────────────────────────────────
# 知识点:
#   - 元组 + 列表拼接: (*tuple1, *list1) 解包语法
#   - django.contrib 是 Django 内置贡献应用

CORE_APPS: tuple[str, ...] = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
)

THIRD_PARTY_APPS: tuple[str, ...] = (
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "django_celery_beat",
)

LOCAL_APPS: tuple[str, ...] = (
    "apps.users",
    "apps.articles",
    "apps.orders",
    "apps.files",
    "apps.logs",
    "apps.dashboard",
)

# 知识点: 元组解包拼接 — 等价于 CORE_APPS + THIRD_PARTY_APPS + LOCAL_APPS
INSTALLED_APPS = [*CORE_APPS, *THIRD_PARTY_APPS, *LOCAL_APPS]

# ─── 中间件 ──────────────────────────────────────────────────
# 知识点:
#   - 中间件是按顺序执行的"洋葱圈"
#   - 请求从上到下走，响应从下到上返

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",        # 必须放前面（CORS 预处理）
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "common.middleware.HealthCheckMiddleware",          # 自定义：健康检查
    "common.middleware.RequestLogMiddleware",          # 自定义：请求日志
    "common.middleware.ResponseTimeMiddleware",        # 自定义：响应时间
]

# ─── URL 配置 ────────────────────────────────────────────────
ROOT_URLCONF = "config.urls"

# ─── 模板 ────────────────────────────────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # 知识点: 列表推导式 [str(p) for p in [...]]
        "DIRS": [str(BASE_DIR / "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "common.context_processors.site_info",  # 自定义上下文
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ─── 数据库 ──────────────────────────────────────────────────
# 知识点: 字典解包 **kwargs
#   DATABASES = {"default": {**db_config, "OPTIONS": {...}}}

DATABASES = {
    "default": {
        "ENGINE": get_env("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": get_env("DB_NAME", "django_admin"),
        "USER": get_env("DB_USER", "postgres"),
        "PASSWORD": get_env("DB_PASSWORD", "postgres"),
        "HOST": get_env("DB_HOST", "localhost"),
        "PORT": get_env("DB_PORT", "5432"),
        "OPTIONS": {
            # 连接池参数 — 生产环境调优
            "pool_size": 10,
            "max_overflow": 20,
        },
    }
}

# ─── 缓存 ────────────────────────────────────────────────────
# 知识点: 字典条件合并
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": get_env("CACHE_REDIS_URL", "redis://localhost:6379/1"),
        "OPTIONS": {
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
        },
        "KEY_PREFIX": "django_admin",
        "TIMEOUT": 300,  # 5 分钟
    }
}

# ─── 认证 ────────────────────────────────────────────────────
AUTH_USER_MODEL = "users.User"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

# JWT 配置
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        hours=int(get_env("JWT_ACCESS_TOKEN_LIFETIME_HOURS", "8"))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(get_env("JWT_REFRESH_TOKEN_LIFETIME_DAYS", "30"))
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer", "JWT"),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_OBTAIN_SERIALIZER": "apps.users.serializers.CustomTokenObtainSerializer",
}

# ─── Django REST Framework ──────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "common.permissions.IsAuthenticatedOrReadOnlyCustom",
    ),
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # 知识点: 异常处理可以自定义
    "EXCEPTION_HANDLER": "common.exceptions.custom_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
    },
    # 版本通过 URL 路径管理（api/v1/…），不做额外 versioning
}

# ─── CORS ────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = get_env(
    "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",")
CORS_ALLOW_CREDENTIALS = True

# ─── drf-spectacular (API 文档) ─────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "Django Admin Backend API",
    "DESCRIPTION": "企业级 Django 后台管理系统 API 文档",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# ─── 静态文件 & 媒体文件 ─────────────────────────────────────
STATIC_URL = get_env("STATIC_URL", "/static/")
STATIC_ROOT = BASE_DIR / get_env("STATIC_ROOT", "staticfiles")
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = get_env("MEDIA_URL", "/media/")
MEDIA_ROOT = BASE_DIR / get_env("MEDIA_ROOT", "media")

# ─── Celery ──────────────────────────────────────────────────
CELERY_BROKER_URL = get_env("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = get_env("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Shanghai"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 分钟

# ─── 日志 ────────────────────────────────────────────────────
# 知识点: 嵌套字典配置 + 自定义过滤器
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module}:{lineno}d {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "filters": ["require_debug_true"],
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# ─── 国际化 ──────────────────────────────────────────────────
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

# ─── 默认主键 ────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
