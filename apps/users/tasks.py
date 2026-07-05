"""
用户模块异步任务。

知识点:
  - @shared_task: Celery 共享任务
  - 异步执行不阻塞请求
  - 可设置重试
"""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def cleanup_expired_users(self) -> dict:
    """
    清理过期用户（示例任务）。

    知识点:
      - bind=True: self 是任务实例
      - max_retries: 最大重试次数
      - default_retry_delay: 重试间隔
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import User

    # 清理 3 年前注册但未登录的闲置用户
    cutoff = timezone.now() - timedelta(days=365 * 3)
    expired_users = User.objects.filter(
        last_login__isnull=True,
        date_joined__lt=cutoff,
        is_active=False,
    )

    count = expired_users.count()
    expired_users.delete()

    logger.info(f"清理了 {count} 个过期用户")
    return {"deleted_count": count}


@shared_task
def send_welcome_email(user_id: str) -> bool:
    """
    发送欢迎邮件（模拟）。

    知识点:
      - 简单任务: 无 bind，纯异步
    """
    try:
        from .models import User
        user = User.objects.get(pk=user_id)
        logger.info(f"发送欢迎邮件给 {user.email}")
        # TODO: 实际邮件发送逻辑
        return True
    except User.DoesNotExist:
        logger.error(f"用户 {user_id} 不存在")
        return False
