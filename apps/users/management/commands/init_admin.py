"""
自定义管理命令 — 初始化超级管理员。

知识点:
  1. BaseCommand: Django 自定义管理命令的基类
  2. Command.handle(): 命令执行入口
  3. Command.help: 命令说明
  4. Command.add_arguments: 自定义命令行参数
  5. `./manage.py init_admin --username admin --password 123456`
"""
from django.core.management.base import BaseCommand, CommandParser
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    """
    初始化超级管理员账号。

    知识点:
      - help 属性: 命令说明
      - add_arguments: 添加命令行参数
      - handle: 命令执行方法
      - self.style.SUCCESS / ERROR: 颜色输出
    """

    help = "初始化超级管理员账号"

    def add_arguments(self, parser: CommandParser) -> None:
        """添加命令行参数。"""
        parser.add_argument(
            "--username",
            type=str,
            default="admin",
            help="管理员用户名",
        )
        parser.add_argument(
            "--password",
            type=str,
            default="admin123",
            help="管理员密码",
        )
        parser.add_argument(
            "--email",
            type=str,
            default="admin@example.com",
            help="管理员邮箱",
        )

    def handle(self, *args, **options) -> None:
        """执行命令。"""
        username = options["username"]
        password = options["password"]
        email = options["email"]

        # 检查是否已存在
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f"用户 '{username}' 已存在，跳过创建")
            )
            return

        # 创建超级管理员
        User.objects.create_superuser(
            username=username,
            password=password,
            email=email,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"超级管理员 '{username}' 创建成功！\n"
                f"  用户名: {username}\n"
                f"  密码: {password}\n"
                f"  邮箱: {email}"
            )
        )
