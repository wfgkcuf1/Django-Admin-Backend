"""
用户信号处理器 — Django Signals 实战。

知识点:
  1. Django Signals: 观察者模式实现
  2. @receiver: 信号装饰器
  3. post_save / pre_save / post_delete / pre_delete
  4. m2m_changed: 多对多关系变化
  5. user_logged_in / user_logged_out: django.contrib.auth 信号
  6. 信号接收函数的参数: sender, instance, created, **kwargs
"""
import logging

from django.contrib.auth.signals import (
    user_logged_in, user_logged_out, user_login_failed
)
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import User

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def user_post_save_handler(sender, instance, created, **kwargs):
    """
    用户保存后信号 — 日志记录。

    知识点:
      - @receiver(post_save, sender=User): 监听 User 的 post_save
      - created: True 表示新创建，False 表示更新
      - **kwargs 包含: update_fields, raw, using 等
    """
    action = "创建" if created else "更新"
    logger.info(f"用户 {action}: {instance.username}({instance.pk})")


@receiver(pre_save, sender=User)
def user_pre_save_handler(sender, instance, **kwargs):
    """
    用户保存前信号 — 数据清洗。

    知识点:
      - pre_save: 保存前触发，可以修改 instance
      - 自动小写用户名
      - 记录旧值
    """
    # 自动小写用户名和邮箱
    if instance.username:
        instance.username = instance.username.lower().strip()
    if instance.email:
        instance.email = instance.email.lower().strip()


@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """
    用户登录成功信号。

    知识点:
      - user_logged_in: django.contrib.auth 发出的信号
      - 更新最后登录时间和 IP
      - 可以在这里做登录后的初始化
    """
    # 更新用户最后登录字段
    User.objects.filter(pk=user.pk).update(
        last_login=timezone.now(),
        last_active_at=timezone.now(),
    )

    # 获取登录 IP
    ip = request.META.get("REMOTE_ADDR", "unknown")
    logger.info(f"用户登录成功: {user.username} 来自 {ip}")


@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    """
    用户登出信号。
    """
    if user and user.is_authenticated:
        logger.info(f"用户登出: {user.username}")


@receiver(user_login_failed)
def user_login_failed_handler(sender, credentials, request, **kwargs):
    """
    用户登录失败信号。

    知识点:
      - credentials: 用户提交的认证信息 dict
      - 可用于记录登录失败次数、IP 封禁等
    """
    username = credentials.get("username", "unknown")
    ip = request.META.get("REMOTE_ADDR", "unknown") if request else "unknown"
    logger.warning(f"用户登录失败: {username} 来自 {ip}")


# ─── 自定义信号 ──────────────────────────────────────────────
# 知识点: 可以自定义信号
from django.dispatch import Signal

# 用户注册信号（额外的自定义信号）
user_registered = Signal()


def send_user_registered_signal(user: User) -> None:
    """
    发送用户注册信号。

    知识点:
      - send(): 发送信号，sender 是发出者
      - 可携带任意关键字参数
    """
    user_registered.send(sender=User, user=user)
    logger.info(f"用户注册信号已发送: {user.username}")
