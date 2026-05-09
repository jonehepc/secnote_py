"""SectionFilterProxy - QSortFilterProxyModel 子类过滤分区树 (D-49)。

通过声明式过滤在视图层分离分区与页面：
- 仅显示 item_type == "section" 的节点
- note 节点在代理模型中不可见
- TreeModel 保持完整数据不变

使用 setRecursiveFilteringEnabled(True) 和 setAutoAcceptChildRows(False)
确保递归过滤正确且 note 子节点不泄露。
"""

from PySide6.QtCore import QModelIndex, QSortFilterProxyModel

from .snote_item import SNoteItem  # noqa: F401 - 用于类型提示


class SectionFilterProxy(QSortFilterProxyModel):
    """过滤代理模型：仅显示 section 类型的节点 (D-49)。

    源模型（TreeModel）包含所有 section 和 note 节点。
    此代理模型过滤后仅保留 section，供 QTreeView 展示分区树。

    Usage:
        proxy = SectionFilterProxy()
        proxy.setSourceModel(tree_model)
        tree_view.setModel(proxy)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # D-49: 递归过滤确保嵌套 section 结构完整保留
        self.setRecursiveFilteringEnabled(True)
        # 关键：防止 note 子节点因父节点被接受而自动泄露
        self.setAutoAcceptChildRows(False)

    def filterAcceptsRow(
        self,
        source_row: int,
        source_parent: QModelIndex = QModelIndex(),
    ) -> bool:
        """决定源模型中第 source_row 行是否应在代理模型中可见。

        过滤规则 (D-49)：
        - 仅接受 item_type == "section" 的节点
        - note 节点永远不可见
        - 防御性：sourceModel() 为 None 或索引无效时返回 False

        Args:
            source_row: 源模型中子节点的行号
            source_parent: 源模型中父节点的 QModelIndex

        Returns:
            True 如果该行应可见，False 否则
        """
        source = self.sourceModel()
        # 防御性检查 (D-49 Open Question #1)
        if source is None:
            return False

        source_index = source.index(source_row, 0, source_parent)
        if not source_index.isValid():
            return False

        item = source_index.internalPointer()
        return item.item_type == "section"
