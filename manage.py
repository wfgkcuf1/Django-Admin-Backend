#!/usr/bin/env python
"""
Django 管理入口 — 项目的启动点。

知识点:
  - shebang `#!/usr/bin/env python`: 跨平台 Python 解释器查找
  - `__file__`: 当前文件路径（魔法变量）
  - sys.path / os.environ: 运行时环境配置
  - `if __name__ == "__main__"`: 模块即脚本的惯用模式
"""
import os
import sys
from pathlib import Path


def main() -> None:
    """
    设置 Django 环境并执行命令行。

    知识点:
      - 类型注解 `-> None`: 函数没有返回值
      - os.environ.setdefault: 只在环境变量未设置时写入（不覆盖已有值）
      - sys.argv: 命令行参数列表，[0] 是脚本名
    """
    # 设置 Django 默认配置文件（优先读环境变量，否则用 dev）
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "config.settings.dev"
    )

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # f-string 调试语法（Python 3.8+）
        raise ImportError(
            f"无法导入 Django，确认是否已安装且环境激活？\n"
            f"当前 Python: {sys.executable}\n"
            f"当前路径: {Path.cwd()}"
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
