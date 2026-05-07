"""Serializer - SNoteItem 树 ↔ JSON 双向转换工具 (D-06)。

职责分离 (D-06)：
- Serializer: to_dict + json.dumps / json.loads + from_dict
- SNoteItem: 纯数据类
- Validator: 规则校验
"""

import json
from dataclasses import asdict

from .snote_item import SNoteItem


class Serializer:
    """SNoteItem 树 ↔ JSON 字符串的双向转换。"""

    FORMAT_VERSION = 1

    @staticmethod
    def to_json(root: SNoteItem) -> str:
        """SNoteItem 树 → JSON 字符串。

        JSON 顶层格式 (D-08, D-11):
        {
            "version": 1,
            "data": { ... }    # 嵌套 SNoteItem 树 (asdict)
        }
        """
        data = asdict(root)
        document = {
            "version": Serializer.FORMAT_VERSION,
            "data": data,
        }
        return json.dumps(document, ensure_ascii=False, indent=2)

    @staticmethod
    def from_json(json_str: str) -> SNoteItem:
        """JSON 字符串 → SNoteItem 树。"""
        document = json.loads(json_str)
        # version 字段保留，未来可用于格式升级检测
        data = document["data"]
        return Serializer._from_dict(data)

    @staticmethod
    def _from_dict(d: dict) -> SNoteItem:
        """递归反序列化 dict → SNoteItem。"""
        children = [Serializer._from_dict(c) for c in d.get("children", [])]
        return SNoteItem(
            id=d["id"],
            title=d["title"],
            item_type=d["item_type"],
            content=d.get("content", ""),
            children=children,
            tags=d.get("tags", []),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
        )
