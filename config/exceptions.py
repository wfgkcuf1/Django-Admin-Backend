"""
配置层自定义异常 — 覆盖 Django 启动时的错误。

知识点:
  - 自定义异常类（继承 Exception）
  - 异常层次结构
"""


class ConfigError(Exception):
    """配置相关错误的基类。"""
    pass


class DatabaseConfigError(ConfigError):
    """数据库配置错误。"""
    pass


class SecurityConfigError(ConfigError):
    """安全配置错误（如密钥未设置）。"""
    pass


class MissingEnvironmentVariable(ConfigError):
    """缺失必要的环境变量。"""

    def __init__(self, var_name: str, hint: str = "") -> None:
        self.var_name = var_name
        msg = f"缺失环境变量: {var_name}"
        if hint:
            msg += f"\n提示: {hint}"
        super().__init__(msg)
