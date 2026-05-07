"""SNoteItem 纯数据类 - SecNotepad 核心数据模型。

SNoteItem 是纯 Python dataclass，不继承任何 Qt 类型 (D-01)。
通过 item_type 字段 ("section" | "note") 区分分区和笔记 (D-02)。
完整字段集遵循 D-03 规范。
"""

from dataclasses import dataclass, field
from typing import List, Optional
import uuid
from datetime import datetime, timezone


@dataclass
class SNoteItem:
    """SecNotepad 笔记项数据类。

    Attributes:
        id: 32 字符 hex UUID (D-05)
        title: 标题
        item_type: "section" (分区) | "note" (笔记) (D-02)
        content: HTML 格式内容 (D-03)
        children: 子节点列表 (D-07: Note 的 children 必须为空)
        tags: 标签列表
        created_at: 创建时间 ISO 8601 (D-10)
        updated_at: 更新时间 ISO 8601 (D-10)
    """

    id: str = ""
    title: str = ""
    item_type: str = "note"  # "section" | "note"
    content: str = ""
    children: List["SNoteItem"] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    @staticmethod
    def create_id() -> str:
        """生成 32 字符 hex UUID (D-05)。"""
        return uuid.uuid4().hex

    @staticmethod
    def now_iso() -> str:
        """生成 ISO 8601 时间戳 (D-10)。"""
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    def new_section(cls, title: str) -> "SNoteItem":
        """创建分区 (item_type="section")。"""
        now = cls.now_iso()
        return cls(
            id=cls.create_id(),
            title=title,
            item_type="section",
            children=[],
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def new_note(cls, title: str, content: str = "") -> "SNoteItem":
        """创建笔记叶子节点 (item_type="note")。

        Note 的 children 必须永远为空 (D-07)。
        """
        now = cls.now_iso()
        return cls(
            id=cls.create_id(),
            title=title,
            item_type="note",
            content=content,
            children=[],
            created_at=now,
            updated_at=now,
        )
