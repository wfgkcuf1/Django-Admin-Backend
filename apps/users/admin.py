"""
Django Admin 配置 — 用户管理后台。

知识点:
  1. ModelAdmin: Django 内置管理后台的配置类
  2. list_display: 列表显示字段
  3. list_filter: 列表筛选
  4. search_fields: 搜索字段
  5. fieldsets: 表单分组
  6. inlines: 内联编辑
  7. actions: 批量操作
  8. readonly_fields: 只读字段
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    用户管理后台。

    知识点:
      - 继承 Django 的 UserAdmin 复用已有的配置
      - 添加自定义字段到 fieldsets
      - 列表页显示更多列
    """

    # ─── 列表页配置 ────────────────────────────────────────
    list_display = [
        "username", "nickname", "email", "phone",
        "role", "is_active", "is_staff", "is_superuser",
        "last_login", "date_joined",
    ]
    list_filter = ["role", "is_active", "is_staff", "is_superuser", "gender"]
    search_fields = ["username", "email", "phone", "nickname"]
    ordering = ["-date_joined"]
    list_per_page = 20

    # ─── 详情页配置 ────────────────────────────────────────
    # 知识点: fieldsets 将表单分组显示
    fieldsets = [
        (
            _("基本信息"),
            {"fields": ["username", "nickname", "password", "avatar"]},
        ),
        (
            _("联系方式"),
            {"fields": ["email", "phone"]},
        ),
        (
            _("权限"),
            {
                "fields": [
                    "role", "is_active", "is_staff", "is_superuser",
                    "groups", "user_permissions",
                ],
                "classes": ["collapse"],  # 可折叠
            },
        ),
        (
            _("时间信息"),
            {
                "fields": [
                    "last_login", "last_active_at", "date_joined",
                ],
                "classes": ["collapse"],
            },
        ),
    ]

    # 知识点: readonly_fields 在详情页不可编辑
    readonly_fields = [
        "last_login", "last_active_at", "date_joined",
    ]

    # ─── 批量操作 ──────────────────────────────────────────
    # 知识点: actions 注册批量操作方法
    actions = ["bulk_enable", "bulk_disable"]

    @admin.action(description="批量启用选中的用户")
    def bulk_enable(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"已启用 {updated} 个用户")

    @admin.action(description="批量禁用选中的用户")
    def bulk_disable(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"已禁用 {updated} 个用户")
