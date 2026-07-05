"""
用户相关验证器。

知识点:
  - 延迟导入: 函数内部 import 避免循环引用
  - 正则验证
  - 自定义验证规则
"""
import re


def validate_phone(phone: str) -> bool:
    """
    手机号验证。

    知识点:
      - re.fullmatch: 完全匹配
      - 返回 bool
    """
    return bool(re.fullmatch(r"^1[3-9]\d{9}$", phone))


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    密码强度验证。

    知识点:
      - 返回元组: (是否通过, 错误信息)
      - 多项检查
    """
    if len(password) < 8:
        return False, "密码长度至少 8 位"

    checks = {
        "大写字母": bool(re.search(r"[A-Z]", password)),
        "小写字母": bool(re.search(r"[a-z]", password)),
        "数字": bool(re.search(r"\d", password)),
        "特殊字符": bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)),
    }

    passed = sum(checks.values())
    if passed < 3:
        failed = [k for k, v in checks.items() if not v]
        return False, f"密码需要包含: {', '.join(failed)}"

    return True, ""
