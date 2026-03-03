
# =============================================================================
# agentic_coder/ui/file_tree.py
# =============================================================================
# ファイルツリー — エージェントのファイル生成状態を視覚化する
# =============================================================================

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from . import theme


_STATUS_ICONS = {
    "pending":  ("⏳", theme.FG_SECONDARY),
    "coding":   ("⚙️",  theme.FG_ACCENT),
    "testing":  ("🧪", "#dcdcaa"),
    "debugging":("🔧", theme.FG_WARNING),
    "complete": ("✅", theme.FG_SUCCESS),
    "failed":   ("❌", theme.FG_ERROR),
}


class FileTreePanel(QTreeWidget):
    """
    エージェントが生成するファイルの状態をリアルタイムで表示するツリーパネル。
    各ファイルの処理状態をアイコンと色で視覚化する。
    """

    def __init__(self) -> None:
        super().__init__()
        self.setHeaderLabels(["File", "Status"])
        self.setColumnWidth(0, 200)
        self.setAlternatingRowColors(True)
        self.setStyleSheet(
            f"QTreeWidget {{ alternate-background-color: {theme.BG_WIDGET}; }}"
        )
        self._items: dict[str, QTreeWidgetItem] = {}

    def add_file(self, filename: str) -> None:
        """
        ファイルをツリーにPENDING状態で追加する。

        Args:
            filename: 追加するファイル名
        """
        if filename in self._items:
            return
        item = QTreeWidgetItem([filename, "⏳ pending"])
        item.setForeground(1, QColor(theme.FG_SECONDARY))
        self.addTopLevelItem(item)
        self._items[filename] = item

    def set_status(self, filename: str, status: str) -> None:
        """
        ファイルの処理状態を更新する。

        Args:
            filename: 対象ファイル名
            status: 新しい状態キー ('coding', 'testing', 'complete', 'failed' など)
        """
        item = self._items.get(filename)
        if not item:
            self.add_file(filename)
            item = self._items[filename]

        icon, color = _STATUS_ICONS.get(status, ("•", theme.FG_PRIMARY))
        item.setText(1, f"{icon} {status}")
        item.setForeground(1, QColor(color))

        # 完了・失敗時はファイル名も色付け
        if status == "complete":
            item.setForeground(0, QColor(theme.FG_SUCCESS))
        elif status == "failed":
            item.setForeground(0, QColor(theme.FG_ERROR))

    def clear_all(self) -> None:
        """ツリーを初期化する — 新しいプロジェクト開始時に呼び出す。"""
        self.clear()
        self._items.clear()