"""Tests for TreeModel - QAbstractItemModel 适配器。

测试覆盖所有 QAbstractItemModel 契约方法以及隐藏根节点模式 (D-04)。
"""

import pytest
from PySide6.QtCore import QModelIndex, Qt

from src.secnotepad.model.snote_item import SNoteItem
from src.secnotepad.model.tree_model import TreeModel


# ── Fixtures ──


@pytest.fixture
def root_item():
    """创建隐藏根节点 (D-04)。"""
    return SNoteItem.new_section("根分区")


@pytest.fixture
def tree_model(root_item):
    """创建 TreeModel 实例."""
    return TreeModel(root_item, parent=None)


@pytest.fixture
def sample_tree():
    """创建 3 层示例树.

    根分区 (hidden)
    └── 工作 (section)
        ├── 周报 (note)
        └── 项目A (section)
            └── 需求文档 (note)
    """
    root = SNoteItem.new_section("根分区")
    work = SNoteItem.new_section("工作")
    report = SNoteItem.new_note("周报")
    project = SNoteItem.new_section("项目A")
    doc = SNoteItem.new_note("需求文档")
    project.children.append(doc)
    work.children.append(report)
    work.children.append(project)
    root.children.append(work)
    return root


# ── Initial state tests ──


class TestTreeModelInitialState:
    """TreeModel 初始状态测试."""

    def test_model_created_with_root(self, root_item, tree_model):
        """模型创建后持有根节点."""
        assert tree_model._root_item is root_item

    def test_initial_row_count_zero(self, tree_model):
        """空根节点时 rowCount(QModelIndex()) 返回 0."""
        assert tree_model.rowCount(QModelIndex()) == 0

    def test_column_count_is_one(self, tree_model):
        """columnCount 返回 1."""
        assert tree_model.columnCount() == 1

    def test_index_for_empty_model(self, tree_model):
        """空模型 index(0, 0, QModelIndex()) 返回无效索引."""
        idx = tree_model.index(0, 0, QModelIndex())
        assert not idx.isValid()


# ── index() tests ──


class TestTreeModelIndex:
    """TreeModel.index() 测试."""

    def test_index_first_child(self, sample_tree):
        """index(0, 0) 返回根的第一个子节点."""
        model = TreeModel(sample_tree)
        idx = model.index(0, 0, QModelIndex())
        assert idx.isValid()
        assert idx.internalPointer().title == "工作"

    def test_index_row_out_of_range(self, sample_tree):
        """index 越界时返回无效索引."""
        model = TreeModel(sample_tree)
        idx = model.index(99, 0, QModelIndex())
        assert not idx.isValid()

    def test_index_column_out_of_range(self, sample_tree):
        """index column 越界时返回无效索引."""
        model = TreeModel(sample_tree)
        idx = model.index(0, 5, QModelIndex())
        assert not idx.isValid()

    def test_index_nested_child(self, sample_tree):
        """index 返回嵌套子节点."""
        model = TreeModel(sample_tree)
        work = model.index(0, 0, QModelIndex())
        report = model.index(0, 0, work)
        assert report.isValid()
        assert report.internalPointer().title == "周报"

    def test_index_deep_nested(self, sample_tree):
        """深度嵌套的 index."""
        model = TreeModel(sample_tree)
        work = model.index(0, 0, QModelIndex())
        project = model.index(1, 0, work)
        doc = model.index(0, 0, project)
        assert doc.isValid()
        assert doc.internalPointer().title == "需求文档"


# ── parent() tests ──


class TestTreeModelParent:
    """TreeModel.parent() 测试."""

    def test_parent_of_invalid_index(self, sample_tree):
        """无效索引的 parent 返回无效索引."""
        model = TreeModel(sample_tree)
        assert not model.parent(QModelIndex()).isValid()

    def test_parent_of_top_level(self, sample_tree):
        """顶级节点的 parent 返回无效索引（隐藏根，D-04）."""
        model = TreeModel(sample_tree)
        work = model.index(0, 0, QModelIndex())
        parent = model.parent(work)
        assert not parent.isValid()  # 根节点隐藏

    def test_parent_of_nested_child(self, sample_tree):
        """二级子节点的 parent 返回其父节点."""
        model = TreeModel(sample_tree)
        work = model.index(0, 0, QModelIndex())
        report = model.index(0, 0, work)
        parent = model.parent(report)
        assert parent.isValid()
        assert parent.internalPointer().title == "工作"

    def test_parent_chain_consistency(self, sample_tree):
        """index → parent → same index 一致性."""
        model = TreeModel(sample_tree)
        work = model.index(0, 0, QModelIndex())
        report = model.index(0, 0, work)
        parent = model.parent(report)
        child = model.index(0, 0, parent)
        assert child.internalPointer() is report.internalPointer()

    def test_parent_of_deep_nested(self, sample_tree):
        """深度嵌套的 parent 链."""
        model = TreeModel(sample_tree)
        work = model.index(0, 0, QModelIndex())
        project = model.index(1, 0, work)
        doc = model.index(0, 0, project)
        # doc -> project
        assert model.parent(doc).internalPointer().title == "项目A"
        # project -> work
        assert model.parent(project).internalPointer().title == "工作"
        # work -> invalid (root hidden)
        assert not model.parent(work).isValid()


# ── rowCount() tests ──


class TestTreeModelRowCount:
    """TreeModel.rowCount() 测试."""

    def test_root_row_count(self, sample_tree):
        """根（QModelIndex()）的 rowCount 为根的子节点数."""
        model = TreeModel(sample_tree)
        assert model.rowCount(QModelIndex()) == 1  # "工作"

    def test_section_row_count(self, sample_tree):
        """Section 的 rowCount 为其 children 数."""
        model = TreeModel(sample_tree)
        work = model.index(0, 0, QModelIndex())
        assert model.rowCount(work) == 2  # "周报", "项目A"

    def test_note_row_count_zero(self, sample_tree):
        """Note 的 rowCount 为 0."""
        model = TreeModel(sample_tree)
        work = model.index(0, 0, QModelIndex())
        report = model.index(0, 0, work)
        assert model.rowCount(report) == 0

    def test_row_count_column_guard(self, sample_tree):
        """column>0 时 rowCount 返回 0（Qt 约定守卫）."""
        model = TreeModel(sample_tree)
        # 使用 createIndex 绕过单列模型的 hasIndex 限制，
        # 测试 rowCount 对 column>0 的防御性处理
        work = model.index(0, 0, QModelIndex())
        work_ptr = work.internalPointer()
        idx_col1 = model.createIndex(0, 1, work_ptr)
        assert model.rowCount(idx_col1) == 0


# ── data() tests ──


class TestTreeModelData:
    """TreeModel.data() 测试."""

    def test_data_title_display_role(self, sample_tree):
        """data() 对 DisplayRole 返回 title."""
        model = TreeModel(sample_tree)
        work = model.index(0, 0, QModelIndex())
        assert model.data(work, Qt.DisplayRole) == "工作"

    def test_data_nested_title_display_role(self, sample_tree):
        """嵌套节点的 title."""
        model = TreeModel(sample_tree)
        work = model.index(0, 0, QModelIndex())
        report = model.index(0, 0, work)
        assert model.data(report, Qt.DisplayRole) == "周报"

    def test_data_invalid_index(self, sample_tree):
        """无效索引的 data 返回 None."""
        model = TreeModel(sample_tree)
        assert model.data(QModelIndex(), Qt.DisplayRole) is None

    def test_data_unknown_role(self, sample_tree):
        """未实现的 role 返回 None."""
        model = TreeModel(sample_tree)
        work = model.index(0, 0, QModelIndex())
        assert model.data(work, Qt.DecorationRole) is None


# ── flags() tests ──


class TestTreeModelFlags:
    """TreeModel.flags() 测试."""

    def test_flags_valid_index(self, sample_tree):
        """有效索引的 flags 包含 ItemIsEnabled 和 ItemIsSelectable."""
        model = TreeModel(sample_tree)
        work = model.index(0, 0, QModelIndex())
        flags = model.flags(work)
        assert flags & Qt.ItemIsEnabled
        assert flags & Qt.ItemIsSelectable

    def test_flags_invalid_index(self, sample_tree):
        """无效索引的 flags 为 NoItemFlags."""
        model = TreeModel(sample_tree)
        assert model.flags(QModelIndex()) == Qt.NoItemFlags


# ── headerData() tests ──


class TestTreeModelHeader:
    """TreeModel.headerData() 测试."""

    def test_header_title(self, sample_tree):
        """headerData(0, Horizontal, DisplayRole) 返回 '笔记分区'."""
        model = TreeModel(sample_tree)
        header = model.headerData(0, Qt.Horizontal, Qt.DisplayRole)
        assert header == "笔记分区"

    def test_header_vertical_returns_none(self, sample_tree):
        """垂直表头返回 None."""
        model = TreeModel(sample_tree)
        assert model.headerData(0, Qt.Vertical, Qt.DisplayRole) is None


# ── Tree walk helpers tests ──


class TestTreeModelHelpers:
    """TreeModel 辅助方法测试."""

    def test_find_parent_root(self, sample_tree):
        """_find_parent 返回根节点."""
        model = TreeModel(sample_tree)
        work = sample_tree.children[0]
        parent = model._find_parent(sample_tree, work)
        assert parent is sample_tree

    def test_find_parent_nested(self, sample_tree):
        """_find_parent 找到嵌套父节点."""
        model = TreeModel(sample_tree)
        doc = sample_tree.children[0].children[1].children[0]
        parent = model._find_parent(sample_tree, doc)
        assert parent is sample_tree.children[0].children[1]

    def test_find_parent_nonexistent(self, sample_tree):
        """_find_parent 对不存在的节点返回 None."""
        model = TreeModel(sample_tree)
        orphan = SNoteItem.new_note("孤儿")
        result = model._find_parent(sample_tree, orphan)
        assert result is None

    def test_child_row_found(self, sample_tree):
        """_child_row 返回子节点索引."""
        model = TreeModel(sample_tree)
        work = sample_tree.children[0]
        report = work.children[0]
        row = model._child_row(work, report)
        assert row == 0

    def test_child_row_not_found(self, sample_tree):
        """_child_row 对不存在的子节点返回 -1."""
        model = TreeModel(sample_tree)
        orphan = SNoteItem.new_note("孤儿")
        row = model._child_row(sample_tree, orphan)
        assert row == -1


# ── Data mutation tests ──


class TestTreeModelMutation:
    """TreeModel 数据变更操作测试."""

    def test_add_item_to_root(self):
        """add_item 添加子节点到根."""
        root = SNoteItem.new_section("根分区")
        model = TreeModel(root)
        item = SNoteItem.new_section("新分区")
        model.add_item(QModelIndex(), item)
        assert model.rowCount(QModelIndex()) == 1
        idx = model.index(0, 0, QModelIndex())
        assert idx.internalPointer().title == "新分区"

    def test_add_item_to_nested(self, sample_tree):
        """add_item 添加子节点到嵌套 section."""
        model = TreeModel(sample_tree)
        work = model.index(0, 0, QModelIndex())
        new_note = SNoteItem.new_note("新笔记")
        model.add_item(work, new_note)
        assert model.rowCount(work) == 3  # 原来2个 + 新增1个
        last_idx = model.index(2, 0, work)
        assert last_idx.internalPointer().title == "新笔记"

    def test_remove_item(self, sample_tree):
        """remove_item 删除子节点."""
        model = TreeModel(sample_tree)
        work = model.index(0, 0, QModelIndex())
        report = model.index(0, 0, work)
        assert model.remove_item(report)
        # rowCount 减少
        assert model.rowCount(work) == 1
        # 第一个子节点变成 "项目A"
        new_first = model.index(0, 0, work)
        assert new_first.internalPointer().title == "项目A"

    def test_remove_invalid_index(self, sample_tree):
        """remove_item 无效索引返回 False."""
        model = TreeModel(sample_tree)
        assert not model.remove_item(QModelIndex())

    def test_remove_last_child(self):
        """删除最后一个子节点."""
        root = SNoteItem.new_section("根")
        root.children.append(SNoteItem.new_section("独生子"))
        model = TreeModel(root)
        child = model.index(0, 0, QModelIndex())
        assert model.remove_item(child)
        assert model.rowCount(QModelIndex()) == 0

    def test_add_after_remove(self, sample_tree):
        """删除后添加，验证状态正确."""
        model = TreeModel(sample_tree)
        work = model.index(0, 0, QModelIndex())
        report = model.index(0, 0, work)
        model.remove_item(report)
        new_item = SNoteItem.new_note("新增")
        model.add_item(work, new_item)
        assert model.rowCount(work) == 2  # "项目A" + "新增"


# ── Hidden root tests ──


class TestTreeModelHiddenRoot:
    """隐藏根节点模式测试 (D-04)."""

    def test_root_not_accessible_via_index(self, root_item):
        """根节点无法通过 index() 访问."""
        model = TreeModel(root_item)
        assert model.rowCount(QModelIndex()) == 0

    def test_root_children_are_top_level(self):
        """根的子节点作为顶级节点出现."""
        root = SNoteItem.new_section("根分区")
        work = SNoteItem.new_section("工作")
        root.children.append(work)
        model = TreeModel(root)
        assert model.rowCount(QModelIndex()) == 1
        idx = model.index(0, 0, QModelIndex())
        assert idx.internalPointer().title == "工作"
        # 隐藏根：顶级节点的 parent 返回无效索引
        assert not model.parent(idx).isValid()

    def test_root_identity(self, root_item):
        """根节点内部存储不变."""
        model = TreeModel(root_item)
        assert model._root_item is root_item
