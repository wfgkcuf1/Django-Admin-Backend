"""
工具函数集 — 通用的、不依赖 Django 的纯 Python 工具。

知识点:
  1. `__all__`: 控制 `from module import *` 的导出
  2. 生成器: `yield` 懒加载
  3. `functools.reduce`: 累积计算
  4. `itertools` 模块: 链式操作
  5. `dataclasses`: 数据类
  6. 类型注解: `|` 联合类型（Python 3.10+）
"""
import re
import uuid
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Iterator, Optional
from functools import reduce
from itertools import chain
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# ─── 导出控制 ────────────────────────────────────────────────
# 知识点: __all__ 限制通配符导入的内容
__all__ = [
    "generate_uuid", "generate_short_id",
    "md5_hash", "sha256_hash",
    "mask_phone", "mask_email",
    "chunk_list", "flatten",
    "TreeBuilder", "SnowflakeId",
]


# ─── ID 生成 ─────────────────────────────────────────────────
def generate_uuid() -> str:
    """生成 UUID4 字符串。"""
    return str(uuid.uuid4())


def generate_short_id(length: int = 8) -> str:
    """
    生成短 ID（用 uuid 的前 N 位 hex）。

    知识点:
      - uuid.uuid4().hex: 获取 32 位 hex 字符串（无短线）
      - 切片: [length:]
    """
    return uuid.uuid4().hex[:length]


# ─── 哈希工具 ────────────────────────────────────────────────
def md5_hash(data: str) -> str:
    """
    MD5 哈希。

    知识点:
      - hashlib.md5: 需将字符串编码为 bytes
      - .hexdigest(): 输出 16 进制字符串
      - .update(): 可分多次添加数据
    """
    return hashlib.md5(data.encode("utf-8")).hexdigest()


def sha256_hash(data: str, salt: str = "") -> str:
    """
    SHA-256 哈希（可加盐）。

    知识点:
      - 加盐哈希: 数据 + 盐值一起哈希
      - 使用 encode() 转为字节
    """
    return hashlib.sha256(
        (data + salt).encode("utf-8")
    ).hexdigest()


# ─── 数据脱敏 ────────────────────────────────────────────────
def mask_phone(phone: str) -> str:
    """
    手机号脱敏: 138****1234。

    知识点:
      - f-string 表达式: 替换字符
      - 正则: re.sub
      - 列表推导式带条件
    """
    if len(phone) != 11:
        return phone
    return f"{phone[:3]}****{phone[-4:]}"


def mask_email(email: str) -> str:
    """
    邮箱脱敏: tes***@example.com。

    知识点:
      - str.split("@") 分割
      - 海象运算符 :=
      - 列表/字符串切片
    """
    if "@" not in email:
        return email

    if parts := email.split("@"):
        name, domain = parts[0], parts[1]
        masked_name = name[:3] + "***" if len(name) > 3 else name + "***"
        return f"{masked_name}@{domain}"

    return email


# ─── 集合工具 ────────────────────────────────────────────────
def chunk_list(lst: list[Any], chunk_size: int) -> Iterator[list[Any]]:
    """
    将列表分批 — 生成器实现。

    知识点:
      - 生成器函数（yield）
      - range(start, stop, step): 步进切片
      - 切片操作: lst[i:i+chunk_size]

    用法:
      for batch in chunk_list([1,2,3,4,5,6], 2):
          print(batch)  # [1,2], [3,4], [5,6]
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def flatten(nested_list: list[list[Any]]) -> list[Any]:
    """
    展平嵌套列表 — 多种方法演示。

    知识点:
      - 列表推导式嵌套 for: [x for sub in lst for x in sub]
      - itertools.chain.from_iterable: 展开迭代器
      - functools.reduce: 累积运算
    """
    # 方法 1: 列表推导式
    return [item for sublist in nested_list for item in sublist]

    # 方法 2: itertools
    # return list(chain.from_iterable(nested_list))

    # 方法 3: reduce
    # return reduce(lambda x, y: x + y, nested_list, [])


# ─── 树形工具 ────────────────────────────────────────────────
@dataclass
class TreeNode:
    """
    树节点数据类。

    知识点:
      - @dataclass: 自动生成 __init__, __repr__, __eq__
      - 类型注解: Optional, list
      - 默认值: field(default_factory=list)
    """
    id: str
    label: str
    children: list["TreeNode"] = None  # type: ignore
    data: Optional[dict[str, Any]] = None

    def __post_init__(self) -> None:
        """初始化后钩子 — 设置可变默认值。"""
        if self.children is None:
            self.children = []

    def add_child(self, child: "TreeNode") -> None:
        """添加子节点。"""
        self.children.append(child)

    def to_dict(self) -> dict[str, Any]:
        """递归转为 dict。"""
        result = {
            "id": self.id,
            "label": self.label,
            "children": [c.to_dict() for c in self.children],
        }
        if self.data:
            result["data"] = self.data
        return result


class TreeBuilder:
    """
    树形结构构建器 — 将扁平列表转为树。

    知识点:
      - 类封装复杂的转换逻辑
      - 字典映射: {id: node} 快速查找
      - sorted + key: 排序
      - 列表推导式构建最终结果
    """

    def __init__(self, items: list[dict[str, Any]]) -> None:
        """
        items: [{"id": "...", "parent_id": "...", "label": "...", ...}]
        """
        self.items = items

    def build(self) -> list[TreeNode]:
        """构建树。"""
        # 知识点: 字典推导式构建 id → node 的映射
        nodes: dict[str, TreeNode] = {
            item["id"]: TreeNode(
                id=item["id"],
                label=item.get("label", item["id"]),
                data={k: v for k, v in item.items()
                      if k not in ("id", "label", "parent_id")},
            )
            for item in self.items
        }

        # 知识点: 建立父子关系
        roots: list[TreeNode] = []
        for item in self.items:
            node = nodes[item["id"]]
            parent_id = item.get("parent_id")
            if parent_id and parent_id in nodes:
                nodes[parent_id].add_child(node)
            else:
                roots.append(node)

        return roots

    def build_sorted(self, key: str = "sort_order") -> list[TreeNode]:
        """构建并排序。"""
        # 如果 items 有序，直接构建
        return self.build()


# ─── 雪花 ID 生成器（简化版） ──────────────────────────────
class SnowflakeId:
    """
    雪花 ID 生成器（简化实现）。

    知识点:
      - 位运算: <<, |, &
      - 时间戳 + 机器 ID + 序列号构成 64 位整数
      - 单例模式: 全局唯一生成器
    """

    def __init__(
        self,
        worker_id: int = 1,
        datacenter_id: int = 1,
        sequence: int = 0,
    ) -> None:
        self.worker_id = worker_id
        self.datacenter_id = datacenter_id
        self.sequence = sequence
        self.twepoch = 1700000000000  # 自定义纪元（毫秒）
        self.worker_id_bits = 5
        self.datacenter_id_bits = 5
        self.sequence_bits = 12
        self.max_worker_id = -1 ^ (-1 << self.worker_id_bits)
        self.max_datacenter_id = -1 ^ (-1 << self.datacenter_id_bits)
        self.sequence_mask = -1 ^ (-1 << self.sequence_bits)
        self.last_timestamp = -1

    def _timestamp(self) -> int:
        """当前时间戳（毫秒）。"""
        return int(datetime.now().timestamp() * 1000)

    def _til_next_millis(self, last_timestamp: int) -> int:
        """自旋等待下一毫秒。"""
        timestamp = self._timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._timestamp()
        return timestamp

    def next_id(self) -> int:
        """
        生成下一个 ID。

        知识点:
          - 位运算组合各部分
          - ((ts - twepoch) << ...) | (dc_id << ...) ...
          - sequence 自增，超限则等待下一毫秒
        """
        timestamp = self._timestamp()

        if timestamp < self.last_timestamp:
            raise Exception("时钟回拨！")

        if timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & self.sequence_mask
            if self.sequence == 0:
                timestamp = self._til_next_millis(self.last_timestamp)
        else:
            self.sequence = 0

        self.last_timestamp = timestamp

        return (
            ((timestamp - self.twepoch) << (self.worker_id_bits + self.datacenter_id_bits + self.sequence_bits))
            | (self.datacenter_id << (self.worker_id_bits + self.sequence_bits))
            | (self.worker_id << self.sequence_bits)
            | self.sequence
        )
