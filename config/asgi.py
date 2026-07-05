"""
ASGI 配置 — 异步部署入口（Uvicorn / Daphne）。

知识点:
  - ASGI: Asynchronous Server Gateway Interface，WSGI 的异步后继
  - 支持 WebSocket、HTTP/2、Server-Sent Events
  - `get_asgi_application()`: Django 4.0+ 默认支持
  - 可以额外注册 ProtocolTypeRouter 处理 WebSocket
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

# ─── 基础 ASGI 应用 ──────────────────────────────────────────
application = get_asgi_application()
