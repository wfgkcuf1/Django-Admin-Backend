# config 包 — Django 项目核心配置
#
# 知识点: `__init__.py` 使目录成为 Python 包
#  - Python 3.3+ 的 namespace package 可以没有 __init__.py
#  - 但有 __init__.py 可以在这里做包初始化、导入控制
#
# 这里我们用 __init__.py 来确保 Celery 应用被自动加载

# 从 .celery 模块导入 Celery 实例
# 这样 `from config import celery_app` 就可以在任何地方使用
from .celery import app as celery_app

__all__ = ["celery_app"]
