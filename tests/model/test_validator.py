"""Tests for Validator - SNoteItem 层级约束校验 (D-06, D-07)."""

import pytest

from src.secnotepad.model.snote_item import SNoteItem
from src.secnotepad.model.validator import ValidationError, Validator


class TestValidationError:
    """ValidationError 异常测试."""

    def test_is_exception(self):
        """ValidationError 是 Exception 的子类."""
        err = ValidationError("test error")
        assert isinstance(err, Exception)
        assert str(err) == "test error"


class TestValidatorSection:
    """Section 节点校验."""

    def test_empty_section_valid(self):
        """空 section（无 children）校验通过."""
        section = SNoteItem.new_section("空分区")
        assert Validator.validate(section) is None

    def test_section_with_notes_valid(self):
        """Section 包含 Note 子节点时校验通过."""
        section = SNoteItem.new_section("工作")
        section.children.append(SNoteItem.new_note("周报"))
        section.children.append(SNoteItem.new_note("日报"))
        assert Validator.validate(section) is None

    def test_section_with_sub_sections_valid(self):
        """Section 嵌套子 Section 时校验通过."""
        parent = SNoteItem.new_section("项目")
        child = SNoteItem.new_section("子项目")
        parent.children.append(child)
        assert Validator.validate(parent) is None

    def test_section_with_mixed_children_valid(self):
        """Section 混合包含 Section 和 Note 时校验通过."""
        section = SNoteItem.new_section("根")
        section.children.append(SNoteItem.new_section("分区"))
        section.children.append(SNoteItem.new_note("笔记"))
        section.children.append(SNoteItem.new_section("另一个分区"))
        assert Validator.validate(section) is None


class TestValidatorNote:
    """Note 节点校验."""

    def test_empty_note_valid(self):
        """空 Note（children 为空）校验通过."""
        note = SNoteItem.new_note("笔记")
        assert Validator.validate(note) is None

    def test_note_with_content_valid(self):
        """Note 有 content 但无 children 时校验通过."""
        note = SNoteItem.new_note("笔记", "<p>内容</p>")
        assert Validator.validate(note) is None

    def test_note_with_children_returns_error(self):
        """Note 有 children 时返回 ValidationError."""
        note = SNoteItem.new_note("非法笔记")
        child = SNoteItem.new_note("子节点")
        note.children.append(child)
        result = Validator.validate(note)
        assert result is not None
        assert isinstance(result, ValidationError)
        assert "非法笔记" in str(result)
        assert "cannot have children" in str(result)


class TestValidatorRecursive:
    """递归校验测试."""

    def test_nested_note_with_children_detected(self):
        """深层嵌套中的非法 Note 被检测到."""
        root = SNoteItem.new_section("根")
        l1 = SNoteItem.new_section("一级")
        l2 = SNoteItem.new_section("二级")
        bad_note = SNoteItem.new_note("非法叶子")
        bad_child = SNoteItem.new_note("不应该存在")

        bad_note.children.append(bad_child)
        l2.children.append(bad_note)
        l1.children.append(l2)
        root.children.append(l1)

        result = Validator.validate(root)
        assert result is not None
        assert "非法叶子" in str(result)
        assert "cannot have children" in str(result)

    def test_deep_valid_tree_returns_none(self):
        """深层有效树返回 None."""
        root = SNoteItem.new_section("根")
        for i in range(3):
            section = SNoteItem.new_section(f"L1-{i}")
            for j in range(2):
                section.children.append(
                    SNoteItem.new_note(f"笔记-{i}-{j}", f"内容{i}{j}")
                )
            root.children.append(section)
        assert Validator.validate(root) is None

    def test_first_error_returned(self):
        """返回第一个检测到的错误."""
        root = SNoteItem.new_section("根")
        good = SNoteItem.new_section("正常")
        bad1 = SNoteItem.new_note("错误1")
        bad1.children.append(SNoteItem.new_note("子"))
        bad2 = SNoteItem.new_note("错误2")
        bad2.children.append(SNoteItem.new_note("子"))

        root.children.append(good)
        root.children.append(bad1)
        root.children.append(bad2)

        result = Validator.validate(root)
        assert result is not None
        # 应返回第一个发现的错误
        assert "错误1" in str(result)


class TestValidatorEdgeCases:
    """校验边界情况."""

    def test_none_item(self):
        """validate(None) 应抛出异常或优雅处理."""
        with pytest.raises(AttributeError):
            Validator.validate(None)  # type: ignore

    def test_section_renamed_to_note_but_has_children(self):
        """item_type 改为 note 但仍有 children 时报错."""
        section = SNoteItem.new_section("原是分区")
        section.children.append(SNoteItem.new_note("子笔记"))
        section.item_type = "note"  # 改为 note 类型但保留 children
        result = Validator.validate(section)
        assert result is not None

    def test_note_converted_to_section_passes(self):
        """Note 改为 section 类型且有 children 时通过."""
        note = SNoteItem.new_note("原是笔记")
        note.item_type = "section"
        note.children.append(SNoteItem.new_note("子"))
        assert Validator.validate(note) is None
