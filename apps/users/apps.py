"""
users 应用配置。

知识点:
  - AppConfig: Django 应用配置类
  - default_auto_field: 默认主键类型
  - name: 应用的 Python 路径
  - verbose_name: admin 中显示的名称
"""
from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"
    verbose_name = "用户管理"

    def ready(self) -> None:
        """
        应用就绪时 — 导入信号处理器。

        知识点:
          - ready() 在 Django 启动时调用
          - 确保 signals.py 被加载（信号消费者注册）
        """
        import apps.users.signals  # noqa: F401
