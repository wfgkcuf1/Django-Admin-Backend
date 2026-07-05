"""
自定义上下文处理器 — 向模板注射全局变量。

知识点:
  1. 上下文处理器是一个接收 request 返回 dict 的函数
  2. 在 settings.TEMPLATES.OPTIONS.context_processors 中注册
  3. 所有模板均可访问返回的 key-value
"""
from datetime import datetime

from django.conf import settings
from django.utils import timezone


def site_info(request) -> dict:
    """
    全局站点信息上下文。

    在模板中可用: {{ site_name }}, {{ current_year }}
    """
    return {
        "site_name": "Django Admin Backend",
        "site_version": "1.0.0",
        "current_year": timezone.now().year,
        "debug": settings.DEBUG,
    }
