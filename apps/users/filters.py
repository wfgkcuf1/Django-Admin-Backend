"""
用户过滤器 — 基于 django-filter 实现高级查询。

知识点:
  1. django-filter: 声明式过滤
  2. FilterSet: 过滤器集合
  3. CharFilter + lookup_expr: 模糊查询
  4. DateFilter / DateTimeFilter: 时间范围
  5. BooleanFilter: 布尔过滤
  6. ChoiceFilter: 枚举选择过滤
  7. NumberFilter: 数字比较
"""
import django_filters
from django.db.models import Q

from .models import User
from common.enums import Gender, UserRole


class UserFilter(django_filters.FilterSet):
    """
    用户列表过滤器。

    知识点:
      - lookup_expr: Django ORM 查询表达式
        - exact: 精确匹配
        - icontains: 不区分大小写包含
        - gt/gte/lt/lte: 大于/小于
      - field_name: 映射到模型字段
      - method: 自定义过滤方法
    """

    # ─── 文本模糊搜索 ──────────────────────────────────────
    # 知识点: icontains 实现模糊搜索（ILIKE）
    username = django_filters.CharFilter(
        field_name="username",
        lookup_expr="icontains",
        help_text="用户名模糊搜索",
    )
    email = django_filters.CharFilter(
        field_name="email",
        lookup_expr="icontains",
        help_text="邮箱模糊搜索",
    )
    phone = django_filters.CharFilter(
        field_name="phone",
        lookup_expr="icontains",
        help_text="手机号模糊搜索",
    )
    nickname = django_filters.CharFilter(
        field_name="nickname",
        lookup_expr="icontains",
        help_text="昵称模糊搜索",
    )

    # ─── 关键字搜索（多字段） ──────────────────────────────
    # 知识点: method 自定义过滤逻辑
    keyword = django_filters.CharFilter(
        method="filter_keyword",
        help_text="全局关键词搜索（用户名/邮箱/手机号/昵称）",
    )

    def filter_keyword(self, queryset, name, value):
        """关键词跨字段搜索。"""
        return queryset.filter(
            Q(username__icontains=value)
            | Q(email__icontains=value)
            | Q(phone__icontains=value)
            | Q(nickname__icontains=value)
        )

    # ─── 精确匹配 ──────────────────────────────────────────
    role = django_filters.ChoiceFilter(
        choices=[(r.value, r.label) for r in UserRole],
        help_text="角色过滤",
    )
    gender = django_filters.ChoiceFilter(
        choices=Gender.choices(),
        help_text="性别过滤",
    )
    is_active = django_filters.BooleanFilter(help_text="启用状态")
    is_staff = django_filters.BooleanFilter(help_text="是否管理员")
    is_superuser = django_filters.BooleanFilter(help_text="是否超级管理员")

    # ─── 时间范围 ──────────────────────────────────────────
    # 知识点: DateTimeFromToRangeFilter 支持时间范围
    date_joined_after = django_filters.DateTimeFilter(
        field_name="date_joined",
        lookup_expr="gte",
        help_text="注册时间 >= ",
    )
    date_joined_before = django_filters.DateTimeFilter(
        field_name="date_joined",
        lookup_expr="lte",
        help_text="注册时间 <= ",
    )
    last_login_after = django_filters.DateTimeFilter(
        field_name="last_login",
        lookup_expr="gte",
        help_text="最后登录 >= ",
    )

    class Meta:
        model = User
        fields = [
            "username", "email", "phone", "nickname",
            "role", "gender", "is_active", "is_staff", "is_superuser",
        ]
