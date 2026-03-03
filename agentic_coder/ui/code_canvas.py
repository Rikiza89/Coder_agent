
# =============================================================================
# agentic_coder/ui/code_canvas.py
# =============================================================================
# コードキャンバス — タブ付きエディタ、diff表示、保存機能を提供する
# =============================================================================

from __future__ import annotations

import difflib
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (QColor, QFont, QSyntaxHighlighter, QTextCharFormat,
                            QTextCursor)
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPlainTextEdit,
                                QPushButton, QSplitter, QTabWidget,
                                QVBoxLayout, QWidget)

from . import theme


class PythonHighlighter(QSyntaxHighlighter):
    """
    シンプルなPython構文ハイライター。
    パフォーマンスを優先し正規表現ベースで実装する。
    """

    _KEYWORDS = (
        "False", "None", "True", "and", "as", "assert", "async", "await",
        "break", "class", "continue", "def", "del", "elif", "else", "except",
        "finally", "for", "from", "global", "if", "import", "in", "is",
        "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
        "while", "with", "yield",
    )

    def __init__(self, document) -> None:
        super().__init__(document)
        import re

        self._rules: list[tuple[re.Pattern, QTextCharFormat]] = []

        def fmt(color: str, bold: bool = False) -> QTextCharFormat:
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(700)
            return f

        # キーワード
        kw_pattern = r"\b(" + "|".join(self._KEYWORDS) + r")\b"
        self._rules.append((re.compile(kw_pattern), fmt(theme.FG_KEYWORD, bold=True)))
        # デコレータ
        self._rules.append((re.compile(r"@\w+"), fmt("#dcdcaa")))
        # 文字列（ダブルクォート）
        self._rules.append((re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*"'), fmt(theme.FG_WARNING)))
        # 文字列（シングルクォート）
        self._rules.append((re.compile(r"'[^'\\]*(?:\\.[^'\\]*)*'"), fmt(theme.FG_WARNING)))
        # コメント
        self._rules.append((re.compile(r"#[^\n]*"), fmt(theme.FG_SECONDARY)))
        # 数値リテラル
        self._rules.append((re.compile(r"\b\d+\.?\d*\b"), fmt("#b5cea8")))
        # 組み込み関数
        builtins = r"\b(print|len|range|type|int|str|float|list|dict|set|tuple|bool|open|super|self)\b"
        self._rules.append((re.compile(builtins), fmt(theme.FG_SUCCESS)))
        # 関数/クラス定義名
        self._rules.append((re.compile(r"(?<=def )\w+"), fmt("#dcdcaa")))
        self._rules.append((re.compile(r"(?<=class )\w+"), fmt(theme.FG_SUCCESS, bold=True)))

    def highlightBlock(self, text: str) -> None:
        """ブロック単位で構文ハイライトを適用する。"""
        for pattern, fmt in self._rules:
            for m in pattern.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


class CodeEditor(QWidget):
    """
    構文ハイライト付きコードエディタタブ。
    編集・保存・diff表示の三機能を持つ。

    Args:
        filename: 表示対象ファイル名
        code: 初期コード内容
        output_dir: 保存先ディレクトリ
    """

    saved = Signal(str)  # 保存完了時にファイル名を送出

    def __init__(self, filename: str, code: str, output_dir: Path) -> None:
        super().__init__()
        self._filename = filename
        self._output_dir = output_dir
        self._diff_visible = False
        self._old_code = ""
        self._setup_ui(code)

    def _setup_ui(self, code: str) -> None:
        """UIコンポーネントを初期化する。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ヘッダーバー
        header = QWidget()
        header.setFixedHeight(32)
        header.setStyleSheet(f"background:{theme.BG_PANEL}; border-bottom:1px solid {theme.BORDER};")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(8, 0, 8, 0)

        lbl = QLabel(self._filename)
        lbl.setStyleSheet(f"color:{theme.FG_SECONDARY}; font-size:9pt;")

        self._btn_diff = QPushButton("⊕ Diff")
        self._btn_diff.setObjectName("btnSecondary")
        self._btn_diff.setFixedHeight(22)
        self._btn_diff.setEnabled(False)
        self._btn_diff.clicked.connect(self._toggle_diff)

        self._btn_save = QPushButton("💾 Save")
        self._btn_save.setFixedHeight(22)
        self._btn_save.clicked.connect(self._save)

        h_layout.addWidget(lbl)
        h_layout.addStretch()
        h_layout.addWidget(self._btn_diff)
        h_layout.addWidget(self._btn_save)
        layout.addWidget(header)

        # エディタ / diff スプリッター
        self._splitter = QSplitter(Qt.Horizontal)

        self._editor = QPlainTextEdit()
        self._editor.setPlainText(code)
        self._editor.setFont(QFont("Consolas", theme.FONT_SIZE_CODE))
        PythonHighlighter(self._editor.document())

        self._diff_view = QPlainTextEdit()
        self._diff_view.setReadOnly(True)
        self._diff_view.setFont(QFont("Consolas", 9))
        self._diff_view.hide()

        self._splitter.addWidget(self._editor)
        self._splitter.addWidget(self._diff_view)
        layout.addWidget(self._splitter)

    def update_code(self, new_code: str, old_code: str = "") -> None:
        """
        エディタのコードを更新し、diffが存在する場合はボタンを有効化する。

        Args:
            new_code: 新しいコード内容
            old_code: diff比較用の旧コード (空文字列の場合diff無効)
        """
        self._editor.setPlainText(new_code)
        self._old_code = old_code
        self._btn_diff.setEnabled(bool(old_code))
        if old_code and self._diff_visible:
            self._render_diff(old_code, new_code)

    def _toggle_diff(self) -> None:
        """diffビューの表示/非表示を切り替える。"""
        self._diff_visible = not self._diff_visible
        if self._diff_visible:
            current = self._editor.toPlainText()
            self._render_diff(self._old_code, current)
            self._diff_view.show()
            self._btn_diff.setText("✕ Diff")
        else:
            self._diff_view.hide()
            self._btn_diff.setText("⊕ Diff")

    def _render_diff(self, old: str, new: str) -> None:
        """unified diff形式でdiffを描画する。"""
        diff = difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile="before",
            tofile="after",
        )
        self._diff_view.setPlainText("".join(diff))

    def _save(self) -> None:
        """エディタ内容をファイルに保存する。"""
        path = self._output_dir / self._filename
        path.write_text(self._editor.toPlainText(), encoding="utf-8")
        self.saved.emit(self._filename)


class CodeCanvas(QTabWidget):
    """
    複数ファイルのタブ付きコードエディタコンテナ。
    ファイル名をキーとしてCodeEditorインスタンスを管理する。

    Args:
        output_dir: ファイル保存先ディレクトリ
    """

    def __init__(self, output_dir: Path) -> None:
        super().__init__()
        self._output_dir = output_dir
        self._tabs: dict[str, int] = {}  # filename → tab index
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self._close_tab)

    def upsert_file(self, filename: str, code: str,
                    is_fix: bool = False, old_code: str = "") -> None:
        """
        ファイルタブを追加または更新する。
        既存タブは内容を更新し、新規は追加する。

        Args:
            filename: ファイル名
            code: 表示するコード
            is_fix: デバッグ修正コードかどうか
            old_code: diff用の旧コード
        """
        if filename in self._tabs:
            idx = self._tabs[filename]
            editor: CodeEditor = self.widget(idx)
            editor.update_code(code, old_code)
            self.setCurrentIndex(idx)
            if is_fix:
                self.setTabText(idx, f"🔧 {filename}")
        else:
            editor = CodeEditor(filename, code, self._output_dir)
            idx = self.addTab(editor, filename)
            self._tabs[filename] = idx
            self.setCurrentIndex(idx)

    def set_output_dir(self, path: Path) -> None:
        """作業ディレクトリが変更されたとき全エディタの保存先を更新する。"""
        self._output_dir = path
        for i in range(self.count()):
            w: CodeEditor = self.widget(i)
            w._output_dir = path

    def _close_tab(self, index: int) -> None:
        """タブを閉じてインデックスマップを更新する。"""
        name = self.tabText(index).lstrip("🔧 ")
        self._tabs.pop(name, None)
        self.removeTab(index)
        # インデックスを再構築
        self._tabs = {
            self.tabText(i).lstrip("🔧 "): i
            for i in range(self.count())
        }