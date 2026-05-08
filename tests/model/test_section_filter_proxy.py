"""Tests for SectionFilterProxy - QSortFilterProxyModel 子类 (D-49)。

验证分区树过滤行为：
- section 节点可见，note 节点不可见
- 递归过滤保留多级嵌套 section
- AutoAcceptChildRows(False) 防止 note 子节点泄露
- 源模型变更自动传播
- mapToSource 正确映射索引
- sourceModel 为 None 时防御性返回 False
"""

import pytest
from PySide6.QtCore import QModelIndex, Qt, QSortFilterProxyModel

from src.secnotepad.model.snote_item import SNoteItem
from src.secnotepad.model.tree_model import TreeModel
from src.secnotepad.model.section_filter_proxy import SectionFilterProxy


# ── Fixtures ──


@pytest.fixture
def root_item():
    """创建隐藏根节点。"""
    return SNoteItem.new_section("根分区")


@pytest.fixture
def tree_model(root_item):
    """创建 TreeModel 实例。"""
    return TreeModel(root_item, parent=None)


@pytest.fixture
def proxy(qapp):
    """创建 SectionFilterProxy 实例。"""
    return SectionFilterProxy()


@pytest.fixture
def three_level_tree():
    """创建 3 层示例树。

    根分区 (section, hidden)
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


@pytest.fixture
def proxy_with_tree(proxy, three_level_tree, qapp):
    """设置 proxy 的源模型为包含数据的 TreeModel。"""
    model = TreeModel(three_level_tree)
    proxy.setSourceModel(model)
    return proxy, model


@pytest.fixture
def note_only_tree():
    """只有 note 没有 section 的树。

    根分区 (section, hidden)
    └── 笔记1 (note)
    └── 笔记2 (note)
    """
    root = SNoteItem.new_section("根分区")
    root.children.append(SNoteItem.new_note("笔记1"))
    root.children.append(SNoteItem.new_note("笔记2"))
    return root


@pytest.fixture
def deep_nested_tree():
    """4 层深层嵌套 section 树。

    根分区 (section, hidden)
    └── A (section)
        └── B (section)
            └── C (section)
                └── D (section)
    """
    root = SNoteItem.new_section("根分区")
    a = SNoteItem.new_section("A")
    b = SNoteItem.new_section("B")
    c = SNoteItem.new_section("C")
    d = SNoteItem.new_section("D")
    c.children.append(d)
    b.children.append(c)
    a.children.append(b)
    root.children.append(a)
    return root


@pytest.fixture
def mixed_nested_tree():
    """深层嵌套 section 中间夹杂 note。

    根分区 (section, hidden)
    └── 工作 (section)
        ├── 日报 (note)
        └── 项目 (section)
            ├── 周报 (note)
            └── 开发 (section)
                ├── 笔记 (note)
                └── 日誌 (note)
    """
    root = SNoteItem.new_section("根分区")
    work = SNoteItem.new_section("工作")
    daily = SNoteItem.new_note("日报")
    project = SNoteItem.new_section("项目")
    weekly = SNoteItem.new_note("周报")
    dev = SNoteItem.new_section("开发")
    dev_note = SNoteItem.new_note("笔记")
    dev_log = SNoteItem.new_note("日誌")
    dev.children.append(dev_note)
    dev.children.append(dev_log)
    project.children.append(weekly)
    project.children.append(dev)
    work.children.append(daily)
    work.children.append(project)
    root.children.append(work)
    return root


# ── filterAcceptsRow 核心行为测试 ──


class TestFilterAcceptsRow:
    """filterAcceptsRow 核心过滤逻辑测试。"""

    def test_accepts_section(self, proxy_with_tree, qapp):
        """场景 1：section 节点 → filterAcceptsRow 返回 True。"""
        proxy, model = proxy_with_tree
        # Root 的第一个子节点是 "工作" section
        source_index = model.index(0, 0, QModelIndex())
        item = source_index.internalPointer()
        assert item.item_type == "section"

        result = proxy.filterAcceptsRow(0, QModelIndex())
        assert result is True

    def test_rejects_note(self, proxy_with_tree, qapp):
        """场景 2：note 节点 → filterAcceptsRow 返回 False。"""
        proxy, model = proxy_with_tree
        # "工作" section 的第一个子节点是 "周报" note
        work_index = model.index(0, 0, QModelIndex())
        report_index = model.index(0, 0, work_index)
        assert report_index.internalPointer().item_type == "note"

        result = proxy.filterAcceptsRow(0, work_index)
        assert result is False

    def test_returns_false_when_source_none(self, proxy, qapp):
        """场景 7：sourceModel 为 None 时 filterAcceptsRow 返回 False，不崩溃。"""
        assert proxy.sourceModel() is None

        result = proxy.filterAcceptsRow(0, QModelIndex())
        assert result is False

    def test_returns_false_for_invalid_index(self, proxy_with_tree, qapp):
        """防御性：无效源索引返回 False。"""
        proxy, model = proxy_with_tree
        # 传入一个不可能的行号
        result = proxy.filterAcceptsRow(999, QModelIndex())
        assert result is False


# ── 代理模型行为测试 ──


class TestProxyModelBehavior:
    """代理模型的整体过滤行为测试。"""

    def test_only_sections_visible(self, proxy_with_tree, qapp):
        """场景 3+4：代理模型仅显示 section 节点，note 不可见。"""
        proxy, model = proxy_with_tree
        # 3 层树：root 隐藏 → 显示 "工作" section
        # "工作" 下应有 "项目A" section（"周报" note 被过滤）
        root_proxy = QModelIndex()
        assert proxy.rowCount(root_proxy) == 1

        work_proxy = proxy.index(0, 0, root_proxy)
        assert work_proxy.isValid()
        work_item = proxy.mapToSource(work_proxy).internalPointer()
        assert work_item.title == "工作"
        assert work_item.item_type == "section"

        # "工作" section 下，代理模型中应仅显示 "项目A" section
        assert proxy.rowCount(work_proxy) == 1
        project_proxy = proxy.index(0, 0, work_proxy)
        project_item = proxy.mapToSource(project_proxy).internalPointer()
        assert project_item.title == "项目A"
        assert project_item.item_type == "section"

    def test_note_children_not_leak(self, proxy_with_tree, qapp):
        """场景 4：autoAcceptChildRows=False —— note 不会泄露到代理模型。"""
        proxy, model = proxy_with_tree
        # 验证 setAutoAcceptChildRows 为 False
        assert proxy.autoAcceptChildRows() is False

        # 递归遍历代理模型，确认没有任何 note 节点
        def collect_types(parent_idx):
            result = set()
            for r in range(proxy.rowCount(parent_idx)):
                child_idx = proxy.index(r, 0, parent_idx)
                src_idx = proxy.mapToSource(child_idx)
                result.add(src_idx.internalPointer().item_type)
                result.update(collect_types(child_idx))
            return result

        types = collect_types(QModelIndex())
        assert "note" not in types
        assert "section" in types

    def test_empty_tree_no_rows(self, proxy, root_item, qapp):
        """边界用例：空树（仅根分区无子节点），代理 rowCount 为 0。"""
        model = TreeModel(root_item)
        proxy.setSourceModel(model)
        assert proxy.rowCount(QModelIndex()) == 0

    def test_only_notes_no_rows(self, proxy, note_only_tree, qapp):
        """边界用例：只有 note 无 section，代理 rowCount 为 0。"""
        model = TreeModel(note_only_tree)
        proxy.setSourceModel(model)
        assert proxy.rowCount(QModelIndex()) == 0

    def test_deep_nesting_sections_visible(self, proxy, deep_nested_tree, qapp):
        """边界用例：4 层深层嵌套 section 全部可见，中间无 note 泄露。"""
        model = TreeModel(deep_nested_tree)
        proxy.setSourceModel(model)

        # 层级遍历验证所有 section 可见
        root_idx = QModelIndex()
        assert proxy.rowCount(root_idx) == 1  # A
        a_idx = proxy.index(0, 0, root_idx)
        assert proxy.rowCount(a_idx) == 1  # B
        b_idx = proxy.index(0, 0, a_idx)
        assert proxy.rowCount(b_idx) == 1  # C
        c_idx = proxy.index(0, 0, b_idx)
        assert proxy.rowCount(c_idx) == 1  # D
        d_idx = proxy.index(0, 0, c_idx)
        assert proxy.rowCount(d_idx) == 0  # D 无子节点

        # 验证节点身份
        assert proxy.mapToSource(a_idx).internalPointer().title == "A"
        assert proxy.mapToSource(b_idx).internalPointer().title == "B"
        assert proxy.mapToSource(c_idx).internalPointer().title == "C"
        assert proxy.mapToSource(d_idx).internalPointer().title == "D"

    def test_mixed_nesting_notes_filtered(self, proxy, mixed_nested_tree, qapp):
        """深层嵌套中夹杂 note：所有 section 可见，所有 note 不可见。"""
        model = TreeModel(mixed_nested_tree)
        proxy.setSourceModel(model)

        # 递归收集代理模型中所有 item_type
        def collect_items(parent_idx):
            items = []
            for r in range(proxy.rowCount(parent_idx)):
                idx = proxy.index(r, 0, parent_idx)
                src_idx = proxy.mapToSource(idx)
                item = src_idx.internalPointer()
                items.append((item.title, item.item_type))
                items.extend(collect_items(idx))
            return items

        all_items = collect_items(QModelIndex())
        titles = [t for t, _ in all_items]
        types = [tp for _, tp in all_items]

        assert all(tp == "section" for tp in types)
        assert "工作" in titles
        assert "项目" in titles
        assert "开发" in titles
        assert "日报" not in titles  # note
        assert "周报" not in titles  # note
        assert "笔记" not in titles  # note
        assert "日誌" not in titles  # note


# ── 源模型变更传播测试 ──


class TestSourceModelChanges:
    """源模型变更自动传播到代理模型。"""

    def test_adding_section_propagates(self, proxy, qapp):
        """场景 5：向 TreeModel 添加新 section 后代理 rowCount 增加。"""
        root = SNoteItem.new_section("根分区")
        root.children.append(SNoteItem.new_section("初始"))
        model = TreeModel(root)
        proxy.setSourceModel(model)

        assert proxy.rowCount(QModelIndex()) == 1

        # 添加新 section
        new_sec = SNoteItem.new_section("新增")
        model.add_item(QModelIndex(), new_sec)

        assert proxy.rowCount(QModelIndex()) == 2

    def test_removing_section_propagates(self, proxy, qapp):
        """删除 section 后代理 model rowCount 减少。"""
        root = SNoteItem.new_section("根分区")
        root.children.append(SNoteItem.new_section("A"))
        root.children.append(SNoteItem.new_section("B"))
        model = TreeModel(root)
        proxy.setSourceModel(model)

        assert proxy.rowCount(QModelIndex()) == 2

        # 删除第一个 section
        proxy_idx = proxy.index(0, 0, QModelIndex())
        src_idx = proxy.mapToSource(proxy_idx)
        model.remove_item(src_idx)

        assert proxy.rowCount(QModelIndex()) == 1


# ── mapToSource / mapFromSource 测试 ──


class TestIndexMapping:
    """索引映射测试。"""

    def test_map_to_source_correct(self, proxy_with_tree, qapp):
        """场景 6：mapToSource 返回源模型中对应的 QModelIndex。"""
        proxy, model = proxy_with_tree
        root_idx = QModelIndex()

        assert proxy.rowCount(root_idx) == 1  # "工作" section
        proxy_idx = proxy.index(0, 0, root_idx)
        src_idx = proxy.mapToSource(proxy_idx)

        assert src_idx.isValid()
        assert src_idx.model() is model
        item = src_idx.internalPointer()
        assert item.title == "工作"
        assert item.item_type == "section"

    def test_map_from_source_correct(self, proxy_with_tree, qapp):
        """mapFromSource 将源模型索引映射回代理模型。"""
        proxy, model = proxy_with_tree
        # 源模型中的 "工作" section 在 root 下 row=0
        src_idx = model.index(0, 0, QModelIndex())
        assert src_idx.internalPointer().title == "工作"

        proxy_idx = proxy.mapFromSource(src_idx)
        assert proxy_idx.isValid()
        # 映射回的代理索引对应同一行
        assert proxy_idx.row() == 0

    def test_map_roundtrip(self, proxy_with_tree, qapp):
        """mapToSource → mapFromSource 往返一致性。"""
        proxy, model = proxy_with_tree
        proxy_idx = proxy.index(0, 0, QModelIndex())

        # Roundtrip: proxy → source → proxy
        src_idx = proxy.mapToSource(proxy_idx)
        roundtrip_proxy = proxy.mapFromSource(src_idx)
        assert roundtrip_proxy.row() == proxy_idx.row()
        assert (proxy.mapToSource(roundtrip_proxy).internalPointer()
                is proxy.mapToSource(proxy_idx).internalPointer())


# ── 配置与初始化测试 ──


class TestSectionFilterProxyInit:
    """SectionFilterProxy 初始化配置测试。"""

    def test_recursive_filtering_enabled(self, proxy, qapp):
        """setRecursiveFilteringEnabled 设置为 True。"""
        assert proxy.isRecursiveFilteringEnabled() is True

    def test_auto_accept_child_rows_disabled(self, proxy, qapp):
        """setAutoAcceptChildRows 设置为 False。"""
        assert proxy.autoAcceptChildRows() is False

    def test_inherits_qsortfilterproxymodel(self, proxy, qapp):
        """SectionFilterProxy 是 QSortFilterProxyModel 的子类。"""
        from PySide6.QtCore import QSortFilterProxyModel
        assert isinstance(proxy, QSortFilterProxyModel)

    def test_source_model_none_initially(self, proxy, qapp):
        """初始状态 sourceModel() 为 None。"""
        assert proxy.sourceModel() is None
