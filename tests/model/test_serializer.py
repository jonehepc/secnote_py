"""Tests for Serializer - SNoteItem 树 ↔ JSON 双向转换."""

import json

import pytest

from src.secnotepad.model.snote_item import SNoteItem
from src.secnotepad.model.serializer import Serializer


# ── Test fixtures ──


@pytest.fixture
def sample_tree():
    """创建 3 层示例树用于序列化测试.

    根分区 (section)
    └── 工作 (section)
        ├── 周报 (note, content="<p>内容1</p>")
        └── 项目A (section)
            └── 需求文档 (note, content="<p>内容2</p>")
    """
    root = SNoteItem.new_section("根分区")
    work = SNoteItem.new_section("工作")
    report = SNoteItem.new_note("周报", "<p>内容1</p>")
    project = SNoteItem.new_section("项目A")
    doc = SNoteItem.new_note("需求文档", "<p>内容2</p>")

    project.children.append(doc)
    work.children.append(report)
    work.children.append(project)
    root.children.append(work)
    return root


# ── to_json tests ──


class TestSerializerToJson:
    """Serializer.to_json() 测试."""

    def test_returns_string(self, sample_tree):
        """to_json() 返回字符串."""
        result = Serializer.to_json(sample_tree)
        assert isinstance(result, str)

    def test_valid_json(self, sample_tree):
        """to_json() 输出可解析的 JSON."""
        result = Serializer.to_json(sample_tree)
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_contains_version(self, sample_tree):
        """JSON 顶层包含 version=1."""
        result = json.loads(Serializer.to_json(sample_tree))
        assert result["version"] == 1

    def test_contains_data(self, sample_tree):
        """JSON 顶层包含 data 字段."""
        result = json.loads(Serializer.to_json(sample_tree))
        assert "data" in result

    def test_data_has_title(self, sample_tree):
        """data 包含根节点 title."""
        result = json.loads(Serializer.to_json(sample_tree))
        assert result["data"]["title"] == "根分区"

    def test_data_has_item_type(self, sample_tree):
        """data 包含 item_type."""
        result = json.loads(Serializer.to_json(sample_tree))
        assert result["data"]["item_type"] == "section"

    def test_children_serialized(self, sample_tree):
        """children 被递归序列化."""
        result = json.loads(Serializer.to_json(sample_tree))
        children = result["data"]["children"]
        assert len(children) == 1
        assert children[0]["title"] == "工作"
        assert len(children[0]["children"]) == 2

    def test_note_content_serialized(self, sample_tree):
        """Note 的 content 被序列化."""
        result = json.loads(Serializer.to_json(sample_tree))
        work = result["data"]["children"][0]
        report = work["children"][0]
        assert report["title"] == "周报"
        assert report["content"] == "<p>内容1</p>"

    def test_tags_field_exists(self, sample_tree):
        """tags 字段存在于序列化输出."""
        result = json.loads(Serializer.to_json(sample_tree))
        assert isinstance(result["data"]["tags"], list)

    def test_snake_case_fields(self, sample_tree):
        """字段使用 snake_case."""
        result = json.loads(Serializer.to_json(sample_tree))
        data = result["data"]
        assert "item_type" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_ensure_ascii_false(self, sample_tree):
        """中文不被转义."""
        result = Serializer.to_json(sample_tree)
        assert "\\u6839" not in result  # "根" 的 unicode 转义


class TestSerializerFromJson:
    """Serializer.from_json() 测试."""

    def test_single_section(self):
        """反序列化单个 section."""
        json_str = json.dumps({
            "version": 1,
            "data": {
                "id": "a" * 32,
                "title": "测试分区",
                "item_type": "section",
                "content": "",
                "children": [],
                "tags": [],
                "created_at": "2026-05-07T10:00:00Z",
                "updated_at": "2026-05-07T10:00:00Z",
            },
        })
        item = Serializer.from_json(json_str)
        assert item.title == "测试分区"
        assert item.item_type == "section"
        assert item.children == []
        assert item.tags == []

    def test_nested_tree_roundtrip(self, sample_tree):
        """Round-trip: tree → JSON → tree' 结构一致."""
        json_str = Serializer.to_json(sample_tree)
        restored = Serializer.from_json(json_str)

        assert restored.title == sample_tree.title
        assert restored.item_type == sample_tree.item_type
        assert len(restored.children) == len(sample_tree.children)
        assert restored.children[0].title == "工作"
        assert restored.children[0].children[0].title == "周报"
        assert restored.children[0].children[0].content == "<p>内容1</p>"
        assert restored.children[0].children[1].title == "项目A"
        assert restored.children[0].children[1].children[0].title == "需求文档"

    def test_roundtrip_preserves_tags(self):
        """Round-trip 保留 tags."""
        item = SNoteItem.new_note("带标签", "内容")
        item.tags = ["重要", "工作"]
        item.tags = ["工作", "紧急"]

        json_str = Serializer.to_json(item)
        restored = Serializer.from_json(json_str)
        assert restored.tags == ["工作", "紧急"]

    def test_from_json_missing_version(self):
        """缺少 version 字段时默认为 1."""
        json_str = json.dumps({
            "data": {
                "id": "b" * 32,
                "title": "无版本",
                "item_type": "note",
                "content": "内容",
                "children": [],
                "tags": [],
                "created_at": "",
                "updated_at": "",
            },
        })
        item = Serializer.from_json(json_str)
        assert item.title == "无版本"

    def test_from_json_missing_optional_fields(self):
        """缺少 tags/created_at/updated_at 等可选字段时使用默认值."""
        json_str = json.dumps({
            "version": 1,
            "data": {
                "id": "c" * 32,
                "title": "最小节点",
                "item_type": "note",
                "content": "hello",
                "children": [],
            },
        })
        item = Serializer.from_json(json_str)
        assert item.tags == []
        assert item.created_at == ""
        assert item.updated_at == ""

    def test_from_json_missing_content(self):
        """缺少 content 时默认为空字符串."""
        json_str = json.dumps({
            "version": 1,
            "data": {
                "id": "d" * 32,
                "title": "无内容",
                "item_type": "note",
                "children": [],
                "tags": [],
                "created_at": "",
                "updated_at": "",
            },
        })
        item = Serializer.from_json(json_str)
        assert item.content == ""

    def test_deeply_nested_roundtrip(self):
        """深层嵌套 round-trip."""
        root = SNoteItem.new_section("根")
        for i in range(3):
            child = SNoteItem.new_section(f"L1-{i}")
            for j in range(2):
                grandchild = SNoteItem.new_note(f"L2-{i}-{j}")
                child.children.append(grandchild)
            root.children.append(child)

        json_str = Serializer.to_json(root)
        restored = Serializer.from_json(json_str)

        assert len(restored.children) == 3
        assert restored.children[0].children[0].title == "L2-0-0"


class TestSerializerEdgeCases:
    """Serializer 边界情况."""

    def test_empty_tree(self):
        """空树（无 children 的 section）可序列化和反序列化."""
        item = SNoteItem.new_section("空分区")
        json_str = Serializer.to_json(item)
        restored = Serializer.from_json(json_str)
        assert restored.title == "空分区"
        assert restored.children == []

    def test_single_note(self):
        """单 Note 节点可 round-trip."""
        item = SNoteItem.new_note("单笔记", "仅内容")
        json_str = Serializer.to_json(item)
        restored = Serializer.from_json(json_str)
        assert restored.title == "单笔记"
        assert restored.content == "仅内容"
