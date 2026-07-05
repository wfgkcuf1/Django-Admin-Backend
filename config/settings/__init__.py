# settings 包 — Django 配置分层
#
# 设计模式: 多环境配置分层
#   base.py → 公共配置（所有环境共享）
#   dev.py  → 开发环境（继承 base，开启调试、SQL 日志）
#   prod.py → 生产环境（继承 base，关闭调试、安全配置）
