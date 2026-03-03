
# =============================================================================
# agentic_coder/ui/app.py
# =============================================================================
# アプリケーションエントリポイント — テーマ適用とウィンドウ起動
# =============================================================================

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from . import theme
from .main_window import MainWindow


def run(orchestrator_factory) -> int:
    """
    PySide6アプリケーションを起動する。

    Args:
        orchestrator_factory: AppConfig → Orchestrator のファクトリ関数

    Returns:
        アプリケーション終了コード
    """
    app = QApplication(sys.argv)
    app.setApplicationName("Agentic Coder")
    app.setApplicationVersion("1.0.0")

    # ダークテーマを全ウィジェットに適用
    app.setStyleSheet(theme.STYLESHEET)
    app.setFont(QFont("Segoe UI", theme.FONT_SIZE_UI))

    window = MainWindow(orchestrator_factory)
    window.show()

    return app.exec()