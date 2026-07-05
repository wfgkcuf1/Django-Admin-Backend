"""
清理闲置用户管理命令。

知识点:
  - 可交互的命令: input() 读用户输入
  - dry-run 模式: 只显示不清除
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "清理长期未登录的闲置用户"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=365,
            help="多少天未登录视为闲置（默认 365）",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="仅预览，不执行删除",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]
        cutoff = timezone.now() - timedelta(days=days)

        expired = User.objects.filter(
            last_login__isnull=True,
            date_joined__lt=cutoff,
            is_active=False,
        )

        count = expired.count()
        self.stdout.write(f"找到 {count} 个闲置用户（{days} 天未登录）")

        if count == 0:
            return

        if dry_run:
            self.stdout.write("（DRY RUN — 未执行删除）")
            for user in expired[:10]:
                self.stdout.write(f"  - {user.username} ({user.date_joined})")
            if count > 10:
                self.stdout.write(f"  ... 还有 {count - 10} 个")
            return

        # 确认删除
        confirm = input(f"确认删除 {count} 个用户？(yes/no): ")
        if confirm.lower() != "yes":
            self.stdout.write("已取消")
            return

        expired.delete()
        self.stdout.write(self.style.SUCCESS(f"已删除 {count} 个闲置用户"))
