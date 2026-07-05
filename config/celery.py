"""
Celery 配置 — 异步任务队列。

知识点:
  - Celery: 分布式任务队列，用于异步/定时任务
  - `@shared_task`: 装饰器，在任何文件中定义任务
  - `autodiscover_tasks()`: 自动发现所有 app 中的 tasks.py
  - `signals` (celery.signals): Celery 的事件钩子
  - 生成器 `yield`: 用于进度回调（Celery 支持进度报告）
"""
import os
from celery import Celery
from django.conf import settings

# ─── 设置 Django 默认配置 ────────────────────────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

# ─── 创建 Celery 应用 ────────────────────────────────────────
app = Celery("django_admin_backend")

# ─── 从 Django settings 加载 Celery 配置 ─────────────────────
# 知识点: namespace="CELERY" 表示所有 Celery 配置项以 CELERY_ 开头
# 例如 settings.CELERY_BROKER_URL 会自动映射为 broker_url
app.config_from_object("django.conf:settings", namespace="CELERY")

# ─── 自动发现所有 app 中的 tasks.py ─────────────────────────
# 知识点: autodiscover_tasks 会在每个 INSTALLED_APPS 中查找 tasks.py
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True, ignore_result=False)
def debug_task(self) -> str:
    """
    调试用任务 — 检查 Celery 是否正常工作。

    知识点:
      - `bind=True`: 将任务实例作为第一个参数 self 传入
      - `self.request`: 访问任务上下文（id, args, kwargs 等）
      - `ignore_result=False`: 保存任务结果
    """
    print(f"✅ Celery 工作正常！请求: {self.request!r}")
    return f"OK - {self.request.id}"
