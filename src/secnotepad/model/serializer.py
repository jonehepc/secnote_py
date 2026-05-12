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
        """JSON 字符串 → SNoteItem 树。

        Raises:
            ValueError: 如果 JSON 格式无效、缺少必填字段或版本不兼容。
        """
        try:
            document = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e
        if not isinstance(document, dict):
            raise ValueError("JSON root must be an object")
        version = document.get("version", 1)
        if version > Serializer.FORMAT_VERSION:
            raise ValueError(
                f"Unsupported format version {version}; "
                f"expected <= {Serializer.FORMAT_VERSION}"
            )
        if "data" not in document:
            raise ValueError("Missing required 'data' field")
        data = document["data"]
        for key in ("id", "title", "item_type"):
            if key not in data:
                raise ValueError(f"Missing required field '{key}' in SNoteItem data")
        return Serializer._from_dict(data)

    @staticmethod
    def _from_dict(d: dict) -> SNoteItem:
        """递归反序列化 dict → SNoteItem。"""
        children = [Serializer._from_dict(c) for c in d.get("children", [])]
        tags = d.get("tags", [])
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            raise ValueError("SNoteItem field 'tags' must be a list of strings")
        return SNoteItem(
            id=d["id"],
            title=d["title"],
            item_type=d["item_type"],
            content=d.get("content", ""),
            children=children,
            tags=tags,
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
        )
