"""
common 公共模块 — 整个项目的共享基础设施。

包含:
  - 基础模型、视图、序列化器
  - 自定义异常、权限、分页
  - 装饰器、中间件、工具函数
  - 常量、枚举、混入类
"""

# 便捷导入
from .enums import *  # noqa: F401, F403
from .constants import *  # noqa: F401, F403
from .exceptions import *  # noqa: F401, F403
