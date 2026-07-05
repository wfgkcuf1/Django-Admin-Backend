"""
根 URL 配置 — 所有路由的总入口。

知识点:
  - `include()` — 包含子路由模块（实现模块化 URL 分发）
  - `path()` vs `re_path()` — 简单路由 vs 正则路由
  - 三元表达式 `x if cond else y` — 条件导入
  - `staticmethod` (`@api_view`) 和类视图
  - drf-spectacular 的 schema 路由
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# ─── API 版本前缀 ────────────────────────────────────────────
API_PREFIX = "api/v1/"

# ─── URL 模式 ────────────────────────────────────────────────
urlpatterns = [
    # Django Admin（后台管理界面）
    path("admin/", admin.site.urls),

    # API: 认证
    path(f"{API_PREFIX}auth/", include("apps.users.urls", namespace="auth")),

    # API: 各业务模块
    path(f"{API_PREFIX}users/", include("apps.users.urls_views", namespace="users")),
    path(f"{API_PREFIX}articles/", include("apps.articles.urls", namespace="articles")),
    path(f"{API_PREFIX}orders/", include("apps.orders.urls", namespace="orders")),
    path(f"{API_PREFIX}files/", include("apps.files.urls", namespace="files")),
    path(f"{API_PREFIX}logs/", include("apps.logs.urls", namespace="logs")),
    path(f"{API_PREFIX}dashboard/", include("apps.dashboard.urls", namespace="dashboard")),
]

# ─── API 文档（仅调试模式） ──────────────────────────────────
if settings.DEBUG:
    from drf_spectacular.views import (
        SpectacularAPIView,
        SpectacularRedocView,
        SpectacularSwaggerView,
    )

    urlpatterns += [
        # OpenAPI schema (JSON/YAML)
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        # Swagger UI
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        # ReDoc UI
        path(
            "api/redoc/",
            SpectacularRedocView.as_view(url_name="schema"),
            name="redoc",
        ),
    ]

# ─── 静态文件 / 媒体文件（仅开发环境） ────────────────────────
# 知识点: static() 函数在 DEBUG=False 时不工作
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
