"""TreeModel - 自定义 QAbstractItemModel 适配器 (D-01, D-04)。

将纯数据类 SNoteItem 树适配到 QTreeView。
数据与视图分离 (D-01)：TreeModel 操作 SNoteItem，不修改数据类。
隐藏根节点模式 (D-04)：_root_item 不对外暴露。
"""

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt

from .snote_item import SNoteItem


class TreeModel(QAbstractItemModel):
    """自定义树模型，适配 SNoteItem → QTreeView (D-01, D-04)。

    内部持有 _root_item（SNoteItem）作为隐藏根节点，所有对外公开的
    索引（QModelIndex）均从根节点的子节点开始。根节点本身不可见。
    """

    def __init__(self, root_item: SNoteItem, parent=None):
        super().__init__(parent)
        self._root_item = root_item  # 隐藏根节点 (D-04)

    # ── QAbstractItemModel 必需契约方法 ──

    def index(self, row: int, column: int,
              parent: QModelIndex = QModelIndex()) -> QModelIndex:
        """创建模型索引。

        通过 internalPointer 存储 SNoteItem 指针，
        后续通过 index.internalPointer() 检索。
        """
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parent_item = (parent.internalPointer()
                       if parent.isValid() else self._root_item)

        if row >= len(parent_item.children):
            return QModelIndex()

        child_item = parent_item.children[row]
        return self.createIndex(row, column, child_item) if child_item else QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        """返回父节点索引。

        对根的子节点（顶级节点）返回无效索引，实现隐藏根 (D-04)。
        使用 _find_parent 遍历树查找父节点。
        """
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = self._find_parent(self._root_item, child_item)

        if parent_item is None or parent_item is self._root_item:
            return QModelIndex()

        # 计算父节点在祖父节点中的行号
        row = self._child_row(self._root_item, parent_item)
        if row == -1:
            # 父节点不是根的直接子节点，需要从上级查找
            grandparent = self._find_parent(self._root_item, parent_item)
            if grandparent is not None:
                row = self._child_row(grandparent, parent_item)
            else:
                return QModelIndex()

        return self.createIndex(row, 0, parent_item)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """返回父节点下的子节点数量。

        Qt 约定守卫：parent.column() > 0 时返回 0。
        """
        if parent.column() > 0:
            return 0

        parent_item = (parent.internalPointer()
                       if parent.isValid() else self._root_item)
        return len(parent_item.children)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """返回列数。SNoteItem 使用单列。"""
        return 1

    def data(self, index: QModelIndex,
             role: int = Qt.DisplayRole):
        """返回索引处的数据显示。

        当前仅支持 DisplayRole（返回 title），
        后续 Phase 可添加 DecorationRole、ToolTipRole 等。
        """
        if not index.isValid():
            return None

        item: SNoteItem = index.internalPointer()
        if role == Qt.DisplayRole:
            return item.title
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section: int,
                   orientation: Qt.Orientation,
                   role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return "笔记分区"
        return None

    # ── 树遍历辅助方法 ──

    @staticmethod
    def _find_parent(root: SNoteItem, target: SNoteItem):
        """在树中递归查找 target 的父节点。

        使用引用比较（is），而非值比较。
        对于少量节点（< 10000）性能可接受。
        返回父节点 SNoteItem，未找到时返回 None。
        """
        for child in root.children:
            if child is target:
                return root
            found = TreeModel._find_parent(child, target)
            if found:
                return found
        return None

    @staticmethod
    def _child_row(parent: SNoteItem, child: SNoteItem) -> int:
        """返回 child 在 parent.children 列表中的索引。

        使用引用比较（is）。
        未找到时返回 -1。
        """
        for i, c in enumerate(parent.children):
            if c is child:
                return i
        return -1

    # ── 数据变更接口（供 Phase 3 调用） ──

    def add_item(self, parent_index: QModelIndex, item: SNoteItem):
        """向指定父节点添加子节点。

        调用前需确保 parent_index 有效（或为 QModelIndex() 表示根）。
        自动发出 beginInsertRows / endInsertRows 信号供视图更新。

        Raises:
            ValueError: 如果父节点是 Note（叶子节点），违反 D-07 规则。
        """
        parent_item = (parent_index.internalPointer()
                       if parent_index.isValid() else self._root_item)
        if parent_item.item_type == "note":
            raise ValueError("Cannot add children to a Note (leaf node)")
        row = len(parent_item.children)
        self.beginInsertRows(parent_index, row, row)
        parent_item.children.append(item)
        self.endInsertRows()

    def remove_item(self, index: QModelIndex) -> bool:
        """删除指定索引的节点及其子树。

        返回 True 表示删除成功，False 表示索引无效。
        自动发出 beginRemoveRows / endRemoveRows 信号。
        """
        if not index.isValid():
            return False
        item = index.internalPointer()
        parent_idx = self.parent(index)
        parent_item = (parent_idx.internalPointer()
                       if parent_idx.isValid() else self._root_item)
        row = self._child_row(parent_item, item)
        if row == -1:
            return False
        self.beginRemoveRows(parent_idx, row, row)
        del parent_item.children[row]
        self.endRemoveRows()
        return True
