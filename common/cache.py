"""
缓存工具 — 封装 Redis 缓存操作。

知识点:
  1. `@contextmanager` 上下文管理器装饰器
  2. 生成器实现上下文管理器: yield 前后分别执行 enter/exit
  3. `functools.partial` 偏函数
  4. `pickle` 序列化
  5. `json` 序列化
"""
import json
import pickle
import logging
from contextlib import contextmanager
from functools import partial
from typing import Any, Callable, Generator, Optional

from django.core.cache import cache

logger = logging.getLogger(__name__)


# ─── 上下文管理器：缓存锁 ────────────────────────────────────
@contextmanager
def cache_lock(lock_key: str, timeout: int = 10) -> Generator[bool, None, None]:
    """
    基于 Redis 的分布式锁上下文管理器。

    知识点:
      - @contextmanager: 用生成器实现上下文管理器
      - try 块 = __enter__, yield = 暂停, finally = __exit__
      - cache.add(): 原子操作，键不存在才设置（实现锁）
      - cache.delete(): 释放锁

    用法:
      with cache_lock("user:123:lock") as acquired:
          if acquired:
              # 执行业务逻辑
              ...
  """
    lock_acquired = False
    try:
        # 知识点: cache.add 是原子操作（SETNX 命令）
        lock_acquired = cache.add(lock_key, "locked", timeout)
        yield lock_acquired
    finally:
        if lock_acquired:
            cache.delete(lock_key)


# ─── 缓存装饰器工厂 ──────────────────────────────────────────
def make_cache_key(prefix: str, *args: Any, **kwargs: Any) -> str:
    """生成统一缓存键。"""
    key = prefix
    if args:
        key += ":" + ":".join(str(a) for a in args)
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        key += ":" + ":".join(f"{k}={v}" for k, v in sorted_kwargs)
    return key


class CacheService:
    """
    缓存服务 — 封装常用缓存操作。

    知识点:
      - 类封装: 所有缓存操作集中管理
      - @staticmethod: 工具方法
      - @classmethod: 工厂方法
      - 泛型: 确保返回值类型安全（但运行时无效果，仅标注）
    """

    @staticmethod
    def get_or_set(
        key: str,
        get_data_func: Callable[[], Any],
        timeout: int = 300,
    ) -> Any:
        """
        读取缓存，未命中则调用函数获取并缓存。

        知识点:
          - 高阶函数: 接收函数作为参数
          - cache.get: 读取
          - cache.set: 写入
        """
        data = cache.get(key)
        if data is not None:
            logger.debug(f"缓存命中: {key}")
            return data

        logger.debug(f"缓存未命中: {key}")
        data = get_data_func()
        if data is not None:
            cache.set(key, data, timeout)
        return data

    @staticmethod
    def bulk_get(keys: list[str]) -> dict[str, Any]:
        """
        批量读取缓存。

        知识点:
          - cache.get_many: 一次性获取多个 key
          - 返回 dict: {key: value, ...}
        """
        return cache.get_many(keys)

    @staticmethod
    def bulk_set(data: dict[str, Any], timeout: int = 300) -> None:
        """
        批量写入缓存。

        知识点:
          - cache.set_many: 一次性设置多个 key
        """
        cache.set_many(data, timeout)

    @staticmethod
    def delete_pattern(pattern: str) -> int:
        """
        按模式删除键（需 Redis 支持 KEYS 命令）。

        知识点:
          - cache.delete_pattern: django-redis 扩展
          - 返回: 删除的数量
        """
        try:
            # 知识点: django-redis 特有的方法
            deleted = cache.delete_pattern(pattern)
            logger.info(f"按模式删除缓存: {pattern} ({deleted} 个)")
            return deleted
        except NotImplementedError:
            logger.warning("当前缓存后端不支持 delete_pattern")
            return 0

    @classmethod
    def clear_model_cache(cls, model_name: str, instance_id: Any) -> None:
        """
        清除某个模型实例的所有缓存。

        知识点:
          - @classmethod: 通过 cls 调用
          - 多个缓存键一并清除
        """
        keys = [
            f"model:{model_name}:{instance_id}",
            f"model:{model_name}:{instance_id}:detail",
        ]
        cache.delete_many(keys)
        logger.info(f"已清除 {model_name}({instance_id}) 的缓存")


# ─── 偏函数应用 ──────────────────────────────────────────────
# 知识点: functools.partial 固定部分参数，生成新函数
cache_one_hour = partial(cache.set, timeout=3600)
cache_one_day = partial(cache.set, timeout=86400)


# ─── 序列化工具 ──────────────────────────────────────────────
class CacheSerializer:
    """
    缓存序列化工具 — 选择最优方式序列化数据。

    知识点:
      - @staticmethod: 独立工具方法
      - try/except 兜底: json 失败则用 pickle
      - isinstance 类型检查
    """

    @staticmethod
    def serialize(data: Any) -> str:
        """序列化为 JSON 字符串。"""
        try:
            return json.dumps(data, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return pickle.dumps(data).hex()

    @staticmethod
    def deserialize(data_str: str) -> Any:
        """反序列化。"""
        try:
            return json.loads(data_str)
        except (json.JSONDecodeError, TypeError):
            return pickle.loads(bytes.fromhex(data_str))
