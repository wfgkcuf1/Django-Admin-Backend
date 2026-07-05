# Django Admin Backend

企业级 Django 后台管理系统 — 学习 Python + Django 的完整项目。

## 快速开始

```bash
# 1. 克隆项目
cd ~/code/django-admin-backend

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，确保数据库配置正确

# 5. 创建数据库
createdb django_admin

# 6. 迁移数据库
python manage.py migrate

# 7. 初始化管理员
python manage.py init_admin --username admin --password admin123

# 8. 创建测试数据（可选）
python manage.py create_users 20
python manage.py loaddata fixtures/initial_data.json

# 9. 启动
python manage.py runserver

# 10. 访问
# API: http://localhost:8000/api/v1/
# Admin: http://localhost:8000/admin/
# 文档: http://localhost:8000/api/docs/
```

## 项目结构

```
django-admin-backend/
├── config/                  # 项目配置
│   ├── settings/
│   │   ├── base.py         # 公共配置
│   │   ├── dev.py          # 开发环境
│   │   └── prod.py         # 生产环境
│   ├── urls.py              # 根路由
│   ├── wsgi.py              # WSGI 入口
│   ├── asgi.py              # ASGI 入口
│   └── celery.py            # Celery 配置
├── apps/                    # 业务应用
│   ├── users/               # 用户认证 & 权限
│   ├── articles/            # 内容管理
│   ├── orders/              # 订单管理
│   ├── files/               # 文件管理
│   ├── logs/                # 操作日志
│   └── dashboard/           # 数据仪表盘
├── common/                  # 公共模块
│   ├── base_model.py        # 基础模型
│   ├── base_view.py         # 基础视图
│   ├── base_serializer.py   # 基础序列化器
│   ├── decorators.py        # 装饰器
│   ├── exceptions.py        # 异常处理
│   ├── enums.py             # 枚举
│   ├── permissions.py       # 权限系统
│   ├── pagination.py        # 分页
│   ├── middleware.py        # 中间件
│   ├── cache.py             # 缓存工具
│   ├── mixins.py            # 混入类
│   └── utils.py             # 工具函数
├── scripts/                 # 脚本
├── media/                   # 上传文件
├── static/                  # 静态文件
├── templates/               # 模板
└── docs/                    # 文档
```

## API 文档

启动后访问:
- Swagger: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- Schema: http://localhost:8000/api/schema/

## API 端点

| 路径 | 方法 | 说明 |
|------|------|------|
| /api/v1/auth/login/ | POST | 登录 |
| /api/v1/auth/register/ | POST | 注册 |
| /api/v1/auth/refresh/ | POST | 刷新 Token |
| /api/v1/users/ | GET/POST | 用户列表/创建 |
| /api/v1/users/me/ | GET | 当前用户信息 |
| /api/v1/users/me/ | PATCH | 更新个人信息 |
| /api/v1/users/{id}/ | GET/PUT/PATCH/DELETE | 用户详情 |
| /api/v1/articles/ | GET/POST | 文章列表/创建 |
| /api/v1/orders/ | GET/POST | 订单列表/创建 |
| /api/v1/files/ | POST | 文件上传 |
| /api/v1/logs/ | GET | 操作日志 |
| /api/v1/dashboard/stats/ | GET | 仪表盘 |
| /health/ | GET | 健康检查 |

## Python 知识点路线图

这个项目演示了以下 Python 核心特性:

### 基础
- 类型注解 (Type Hints)
- 函数/类/模块/包
- 列表/字典/集合推导式
- 海象运算符 `:=` (PEP 572)

### 进阶
- 装饰器 (Decorators)
- 生成器 (Generators)
- 上下文管理器 (Context Managers)
- 元类 & `__init_subclass__`
- `__slots__`, `__str__`, `__repr__`, `__call__`

### 高阶
- 混入类 (Mixin) & MRO
- 泛型 (Generic)
- 数据类 (Dataclasses)
- 枚举 (Enum / IntEnum / StrEnum)
- 异常层次结构
- 信号 (Signals)

### 并发 & IO
- async/await
- Celery 异步任务
- Redis 缓存
- PostgreSQL 连接池

## 管理命令

```bash
# 初始化管理员
python manage.py init_admin --username admin --password admin123

# 批量创建测试用户
python manage.py create_users 50 --prefix test

# 清理闲置用户
python manage.py cleanup_users --days 365 --dry-run
```
