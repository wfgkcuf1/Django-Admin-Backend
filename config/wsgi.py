"""
WSGI 配置 — 同步部署入口（Gunicorn / uWSGI）。

知识点:
  - WSGI: Web Server Gateway Interface，Python Web 应用的标准协议
  - `get_wsgi_application()`: Django 提供的 WSGI 兼容应用工厂
  - `environ.setdefault`: 安全设置环境变量
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_wsgi_application()
