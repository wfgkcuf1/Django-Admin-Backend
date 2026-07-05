"""
自定义装饰器 — Python 装饰器高阶用法。

知识点:
  1. 简单装饰器: `@decorator`
  2. 带参装饰器: `@decorator(args)`
  3. `functools.wraps`: 保留原函数的元信息（name, doc 等）
  4. 类装饰器: `__call__` 实现
  5. 嵌套装饰器: 多个装饰器组合
  6. 异步装饰器: `async def` 支持
  7. `inspect` 模块: 检查函数签名
"""
import asyncio
import functools
import logging
import time
from typing import Any, Callable, Optional, TypeVar, ParamSpec

# 知识点: ParamSpec + TypeVar — 泛型装饰器类型标注（PEP 612）
P = ParamSpec("P")
R = TypeVar("R")

logger = logging.getLogger(__name__)


# ─── 简单装饰器（无参数） ────────────────────────────────────
def timer(func: Callable[P, R]) -> Callable[P, R]:
    """
    函数执行计时装饰器。

    知识点:
      - @functools.wraps(func): 复制 func 的 __name__, __doc__ 等属性
      - *args, **kwargs: 透传所有参数
      - time.perf_counter: 高精度计时器
    """
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        # 知识点: 海象运算符 :=
        if (start := time.perf_counter()) is not None:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logger.debug(f"{func.__name__} 耗时: {elapsed * 1000:.2f}ms")
            return result
        return func(*args, **kwargs)

    return wrapper


# ─── 带参数装饰器（可关闭） ───────────────────────────────────
def log_execution(
    level: str = "DEBUG",
    logger_name: Optional[str] = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    带参数的日志装饰器 — 记录函数调用和返回。

    知识点:
      - 三层嵌套: 最外层接收参数，中间层接收函数，里层接收函数参数
      - logging.getLogger: 可指定日志器
      - 调用/返回/异常三种场景的日志

    用法:
      @log_execution(level="INFO")
      def my_func(x: int) -> int:
          return x * 2
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        log = logging.getLogger(logger_name or func.__module__)

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            log.log(
                getattr(logging, level.upper(), logging.DEBUG),
                f"调用 {func.__qualname__} args={args} kwargs={kwargs}",
            )
            try:
                result = func(*args, **kwargs)
                log.log(
                    getattr(logging, level.upper(), logging.DEBUG),
                    f"{func.__qualname__} 返回 {result!r}",
                )
                return result
            except Exception as e:
                log.error(f"{func.__qualname__} 异常: {e}", exc_info=True)
                raise

        return wrapper

    return decorator


# ─── 类装饰器 ────────────────────────────────────────────────
class Retry:
    """
    重试装饰器（类实现）— 失败时自动重试。

    知识点:
      - 类实现 `__call__`: 实例可被调用（类似函数）
      - `__init__`: 接收装饰器参数
      - asyncio.sleep: 异步等待（如果用在异步函数中）
      - time.sleep: 同步等待

    用法:
      @Retry(max_attempts=3, delay=1.0)
      def unstable_api_call():
          ...
    """

    def __init__(
        self,
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: tuple[type[Exception], ...] = (Exception,),
    ) -> None:
        """
        知识点:
          - dataclass 风格的 __init__（手动编写的）
          - backoff: 退避因子，每次重试等待时间翻倍
        """
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff = backoff
        self.exceptions = exceptions

    def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
        """使实例可调用。"""
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # 知识点: enumerate 从 1 开始计数
            last_exception = None
            current_delay = self.delay

            for attempt in range(1, self.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except self.exceptions as e:
                    last_exception = e
                    if attempt < self.max_attempts:
                        logger.warning(
                            f"{func.__name__} 第 {attempt} 次尝试失败: {e}"
                            f"，{current_delay:.1f}s 后重试..."
                        )
                        time.sleep(current_delay)
                        current_delay *= self.backoff

            logger.error(
                f"{func.__name__} 重试 {self.max_attempts} 次后仍然失败"
            )
            raise last_exception  # type: ignore

        # 知识点: 支持异步函数吗？可以在这里检查
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                current_delay = self.delay
                last_exception = None
                for attempt in range(1, self.max_attempts + 1):
                    try:
                        return await func(*args, **kwargs)
                    except self.exceptions as e:
                        last_exception = e
                        if attempt < self.max_attempts:
                            logger.warning(
                                f"{func.__name__} 第 {attempt} 次尝试失败: {e}"
                            )
                            await asyncio.sleep(current_delay)
                            current_delay *= self.backoff
                raise last_exception  # type: ignore
            return async_wrapper  # type: ignore

        return wrapper


# ─── 缓存装饰器 ──────────────────────────────────────────────
def cached(timeout: int = 300, key_prefix: str = "cache"):
    """
    函数结果缓存装饰器。

    知识点:
      - functools.lru_cache: LRU 缓存（内存中）
      - 但这里演示用 Redis 缓存（分布式场景）
      - cache_key: 基于函数名 + 参数生成
    """
    from django.core.cache import cache

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # 知识点: 生成缓存键
            key = f"{key_prefix}:{func.__name__}:{args}:{kwargs}"
            result = cache.get(key)
            if result is not None:
                return result  # type: ignore

            result = func(*args, **kwargs)
            cache.set(key, result, timeout)
            return result

        return wrapper

    return decorator


# ─── 权限检查装饰器 ──────────────────────────────────────────
def require_permission(*permissions: str):
    """
    权限检查装饰器（用于函数视图）。

    知识点:
      - 直接检查 request.user.has_perm()
      - 如果无权限返回 403

    用法:
      @require_permission("users.delete_user", "users.view_user")
      def my_view(request):
          ...
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(request, *args: P.args, **kwargs: P.kwargs) -> R:
            if not request.user.is_authenticated:
                from common.response import fail
                return fail(message="未登录", code=401)  # type: ignore

            # 知识点: all() + 列表推导式 — 检查所有权限
            if all(request.user.has_perm(perm) for perm in permissions):
                return func(request, *args, **kwargs)

            from common.response import fail
            return fail(message="无权限", code=403)  # type: ignore

        return wrapper

    return decorator
