"""
批量创建测试用户。

知识点:
  - 列表循环处理
  - progress 显示进度
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "批量创建测试用户"

    def add_arguments(self, parser):
        parser.add_argument("count", type=int, nargs="?", default=10)
        parser.add_argument("--prefix", type=str, default="test_user")

    def handle(self, *args, **options):
        count = options["count"]
        prefix = options["prefix"]
        created = 0

        for i in range(1, count + 1):
            username = f"{prefix}_{i:03d}"
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    password="password123",
                )
                created += 1
                if created % 10 == 0:
                    self.stdout.write(f"  已创建 {created} 个用户...")

        self.stdout.write(
            self.style.SUCCESS(f"成功创建 {created} 个测试用户")
        )
