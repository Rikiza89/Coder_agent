
# =============================================================================
# agentic_coder/ui/log_panel.py
# =============================================================================
# ログパネル — エージェントログをリアルタイムストリーミング表示する
# =============================================================================

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPlainTextEdit,
                                QPushButton, QWidget, QVBoxLayout)

from . import theme

# ログレベル → 色マッピング
_LEVEL_COLORS = {
    "DEBUG":    theme.FG_SECONDARY,
    "INFO":     theme.FG_PRIMARY,
    "WARNING":  theme.FG_WARNING,
    "ERROR":    theme.FG_ERROR,
    "CRITICAL": "#ff0000",
}


class LogPanel(QWidget):
    """
    エージェント実行ログをリアルタイムで色付き表示するパネル。
    ログレベルに応じて行色を変え、クリアボタンも提供する。
    """

    _MAX_LINES = 2000  # メモリ保護のための最大行数

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ヘッダー
        header = QWidget()
        header.setFixedHeight(28)
        header.setStyleSheet(f"background:{theme.BG_PANEL}; border-top:1px solid {theme.BORDER};")
        h = QHBoxLayout(header)
        h.setContentsMargins(8, 0, 8, 0)
        h.addWidget(QLabel("OUTPUT"))
        h.addStretch()

        btn_clear = QPushButton("Clear")
        btn_clear.setObjectName("btnSecondary")
        btn_clear.setFixedHeight(20)
        # self._log はまだ未生成のためここでは接続しない
        h.addWidget(btn_clear)
        layout.addWidget(header)

        self._log = QPlainTextEdit()
        self._log.setObjectName("logPanel")
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Consolas", 9))
        self._log.setMaximumBlockCount(self._MAX_LINES)
        layout.addWidget(self._log)

        # _log生成後に接続 — 初期化順序の依存を解決する
        btn_clear.clicked.connect(self._log.clear)

    def append(self, message: str) -> None:
        """
        ログメッセージを色付きで追記する。
        ログレベルを自動検出して行色を決定する。

        Args:
            message: フォーマット済みログ文字列
        """
        color = theme.FG_PRIMARY
        for level, c in _LEVEL_COLORS.items():
            if f"| {level}" in message or f"|{level}" in message:
                color = c
                break

        cursor = self._log.textCursor()
        cursor.movePosition(QTextCursor.End)

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        cursor.insertText(message + "\n")

        # 常に最新行にスクロール
        self._log.setTextCursor(cursor)
        self._log.ensureCursorVisible()