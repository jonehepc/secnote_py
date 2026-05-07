"""Tests for SNoteItem dataclass."""

import uuid
from datetime import datetime, timezone

import pytest

from src.secnotepad.model.snote_item import SNoteItem


class TestSNoteItemCreation:
    """SNoteItem 默认构造和工厂方法测试."""

    def test_default_construction(self):
        """默认构造：id 为空字符串，item_type 为 'note'."""
        item = SNoteItem()
        assert item.id == ""
        assert item.title == ""
        assert item.item_type == "note"
        assert item.content == ""
        assert item.children == []
        assert item.tags == []
        assert item.created_at == ""
        assert item.updated_at == ""

    def test_create_id_returns_32_char_hex(self):
        """create_id() 返回 32 字符 hex UUID，无连字符."""
        id_str = SNoteItem.create_id()
        assert isinstance(id_str, str)
        assert len(id_str) == 32
        # 验证是合法的 hex 字符串
        int(id_str, 16)
        # 无连字符
        assert "-" not in id_str

    def test_create_id_uniqueness(self):
        """连续调用 create_id() 返回不同值."""
        ids = {SNoteItem.create_id() for _ in range(100)}
        assert len(ids) == 100

    def test_now_iso_returns_iso8601(self):
        """now_iso() 返回 ISO 8601 格式字符串."""
        ts = SNoteItem.now_iso()
        assert isinstance(ts, str)
        # 验证可以解析为 datetime
        parsed = datetime.fromisoformat(ts)
        assert parsed.tzinfo is not None

    def test_new_section_creates_section(self):
        """new_section() 创建 item_type='section' 的节点."""
        item = SNoteItem.new_section("工作笔记")
        assert item.title == "工作笔记"
        assert item.item_type == "section"
        assert item.content == ""
        assert item.children == []
        assert item.tags == []
        assert len(item.id) == 32
        int(item.id, 16)  # valid hex
        assert item.created_at != ""
        assert item.updated_at != ""
        assert item.created_at == item.updated_at

    def test_new_note_creates_note(self):
        """new_note() 创建 item_type='note' 的叶子节点."""
        item = SNoteItem.new_note("会议记录", "今天开会讨论了...")
        assert item.title == "会议记录"
        assert item.item_type == "note"
        assert item.content == "今天开会讨论了..."
        assert item.children == []
        assert item.tags == []
        assert len(item.id) == 32

    def test_new_note_default_content_empty(self):
        """new_note() 不传 content 时 content 默认为空字符串."""
        item = SNoteItem.new_note("空笔记")
        assert item.content == ""

    def test_new_section_generates_id(self):
        """new_section() 自动生成唯一 ID."""
        s1 = SNoteItem.new_section("A")
        s2 = SNoteItem.new_section("B")
        assert s1.id != s2.id


class TestSNoteItemMutableDefault:
    """mutable default 防护测试."""

    def test_children_not_shared(self):
        """两个独立实例不共享 children 列表."""
        a = SNoteItem.new_section("A")
        b = SNoteItem.new_section("B")
        a.children.append(SNoteItem.new_note("child"))
        assert len(b.children) == 0

    def test_tags_not_shared(self):
        """两个独立实例不共享 tags 列表."""
        a = SNoteItem.new_note("A")
        b = SNoteItem.new_note("B")
        a.tags.append("重要")
        assert len(b.tags) == 0


class TestSNoteItemNesting:
    """SNoteItem 嵌套结构测试."""

    def test_section_can_contain_notes(self):
        """Section 可以包含 Note 子节点."""
        section = SNoteItem.new_section("工作")
        note = SNoteItem.new_note("周报")
        section.children.append(note)
        assert len(section.children) == 1
        assert section.children[0].title == "周报"
        assert section.children[0].item_type == "note"

    def test_section_can_contain_sub_sections(self):
        """Section 可以包含子 Section."""
        parent = SNoteItem.new_section("项目")
        child = SNoteItem.new_section("子项目")
        parent.children.append(child)
        assert len(parent.children) == 1
        assert parent.children[0].item_type == "section"

    def test_deep_nesting(self):
        """多级嵌套."""
        root = SNoteItem.new_section("根")
        l1 = SNoteItem.new_section("级别1")
        l2 = SNoteItem.new_section("级别2")
        l3 = SNoteItem.new_note("级别3")
        root.children.append(l1)
        l1.children.append(l2)
        l2.children.append(l3)
        assert root.children[0].children[0].children[0].title == "级别3"


class TestSNoteItemFieldAssignment:
    """字段赋值测试."""

    def test_set_title(self):
        item = SNoteItem.new_section("原始")
        item.title = "修改后"
        assert item.title == "修改后"

    def test_set_content(self):
        item = SNoteItem.new_note("笔记")
        item.content = "<p>富文本内容</p>"
        assert item.content == "<p>富文本内容</p>"

    def test_set_tags(self):
        item = SNoteItem.new_note("笔记")
        item.tags = ["工作", "重要"]
        assert item.tags == ["工作", "重要"]

    def test_set_item_type(self):
        item = SNoteItem.new_note("笔记")
        item.item_type = "section"
        assert item.item_type == "section"


class TestSNoteItemWithArgs:
    """通过构造函数传参."""

    def test_construct_with_all_fields(self):
        now = SNoteItem.now_iso()
        child = SNoteItem.new_note("子笔记")
        item = SNoteItem(
            id=SNoteItem.create_id(),
            title="完整节点",
            item_type="section",
            content="<p>内容</p>",
            children=[child],
            tags=["tag1"],
            created_at=now,
            updated_at=now,
        )
        assert item.title == "完整节点"
        assert len(item.children) == 1
        assert len(item.tags) == 1

    def test_custom_id(self):
        custom_id = "aabbccdd00112233445566778899aabb"
        item = SNoteItem(id=custom_id, title="自定义ID")
        assert item.id == custom_id
