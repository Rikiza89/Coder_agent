
# =============================================================================
# agentic_coder/ui/theme.py
# =============================================================================
# VSCodeスタイルのダークテーマ定義 — 単一の色彩ソース
# =============================================================================

from __future__ import annotations

# カラーパレット定数 — 全UIコンポーネントが参照する単一ソース
BG_DEEP    = "#1e1e1e"   # メイン背景
BG_PANEL   = "#252526"   # パネル背景
BG_WIDGET  = "#2d2d30"   # ウィジェット背景
BG_INPUT   = "#3c3c3c"   # 入力フィールド背景
BG_HOVER   = "#094771"   # ホバー状態
BG_SELECT  = "#0e639c"   # 選択状態

FG_PRIMARY   = "#d4d4d4"  # 主テキスト
FG_SECONDARY = "#858585"  # 補助テキスト
FG_ACCENT    = "#569cd6"  # アクセント（青）
FG_SUCCESS   = "#4ec9b0"  # 成功（緑青）
FG_WARNING   = "#ce9178"  # 警告（橙）
FG_ERROR     = "#f44747"  # エラー（赤）
FG_KEYWORD   = "#c586c0"  # キーワード（紫）

BORDER       = "#3e3e42"  # ボーダー色
SCROLLBAR    = "#424242"  # スクロールバー

FONT_MONO    = "Consolas, 'Courier New', monospace"
FONT_UI      = "Segoe UI, Arial, sans-serif"
FONT_SIZE_UI = 10
FONT_SIZE_CODE = 12


STYLESHEET = f"""
/* ベースウィジェット */
QWidget {{
    background-color: {BG_DEEP};
    color: {FG_PRIMARY};
    font-family: {FONT_UI};
    font-size: {FONT_SIZE_UI}pt;
    border: none;
}}

/* メインウィンドウ */
QMainWindow {{
    background-color: {BG_DEEP};
}}

/* メニューバー */
QMenuBar {{
    background-color: {BG_PANEL};
    color: {FG_PRIMARY};
    border-bottom: 1px solid {BORDER};
    padding: 2px;
}}
QMenuBar::item {{
    background: transparent;
    padding: 4px 10px;
    border-radius: 3px;
}}
QMenuBar::item:selected {{
    background-color: {BG_HOVER};
}}
QMenu {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER};
    padding: 4px;
}}
QMenu::item {{
    padding: 5px 20px 5px 10px;
    border-radius: 3px;
}}
QMenu::item:selected {{
    background-color: {BG_SELECT};
}}
QMenu::separator {{
    height: 1px;
    background: {BORDER};
    margin: 3px 0;
}}

/* ツールバー */
QToolBar {{
    background-color: {BG_PANEL};
    border-bottom: 1px solid {BORDER};
    spacing: 4px;
    padding: 2px 6px;
}}
QToolButton {{
    background: transparent;
    border-radius: 4px;
    padding: 4px 8px;
    color: {FG_PRIMARY};
}}
QToolButton:hover {{
    background-color: {BG_HOVER};
}}
QToolButton:pressed {{
    background-color: {BG_SELECT};
}}

/* ステータスバー */
QStatusBar {{
    background-color: {BG_SELECT};
    color: white;
    font-size: 9pt;
    padding: 0 6px;
}}
QStatusBar::item {{
    border: none;
}}

/* スプリッター */
QSplitter::handle {{
    background-color: {BORDER};
}}
QSplitter::handle:horizontal {{
    width: 2px;
}}
QSplitter::handle:vertical {{
    height: 2px;
}}

/* ツリービュー */
QTreeWidget {{
    background-color: {BG_PANEL};
    border: none;
    outline: none;
    font-size: {FONT_SIZE_UI}pt;
}}
QTreeWidget::item {{
    padding: 3px 4px;
    border-radius: 3px;
}}
QTreeWidget::item:hover {{
    background-color: {BG_WIDGET};
}}
QTreeWidget::item:selected {{
    background-color: {BG_SELECT};
    color: white;
}}
QTreeWidget QHeaderView::section {{
    background-color: {BG_PANEL};
    color: {FG_SECONDARY};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 4px;
    font-size: 9pt;
    text-transform: uppercase;
}}

/* タブウィジェット */
QTabWidget::pane {{
    border: none;
    background-color: {BG_DEEP};
}}
QTabBar::tab {{
    background-color: {BG_PANEL};
    color: {FG_SECONDARY};
    padding: 6px 14px;
    border-right: 1px solid {BORDER};
    font-size: {FONT_SIZE_UI}pt;
    min-width: 80px;
}}
QTabBar::tab:selected {{
    background-color: {BG_DEEP};
    color: {FG_PRIMARY};
    border-top: 2px solid {FG_ACCENT};
}}
QTabBar::tab:hover:!selected {{
    background-color: {BG_WIDGET};
    color: {FG_PRIMARY};
}}
QTabBar::tab:close-button {{
    image: none;
}}

/* テキストエディタ */
QPlainTextEdit, QTextEdit {{
    background-color: {BG_DEEP};
    color: {FG_PRIMARY};
    border: none;
    font-family: {FONT_MONO};
    font-size: {FONT_SIZE_CODE}pt;
    selection-background-color: {BG_SELECT};
    padding: 4px;
}}

/* 入力フィールド */
QLineEdit, QTextEdit#requestInput {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 6px 8px;
    color: {FG_PRIMARY};
    font-size: {FONT_SIZE_UI}pt;
    selection-background-color: {BG_SELECT};
}}
QLineEdit:focus, QTextEdit#requestInput:focus {{
    border: 1px solid {FG_ACCENT};
}}

/* ボタン */
QPushButton {{
    background-color: {BG_SELECT};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 14px;
    font-size: {FONT_SIZE_UI}pt;
}}
QPushButton:hover {{
    background-color: #1177bb;
}}
QPushButton:pressed {{
    background-color: #0a5a8e;
}}
QPushButton:disabled {{
    background-color: {BG_WIDGET};
    color: {FG_SECONDARY};
}}
QPushButton#btnDanger {{
    background-color: #6e1111;
}}
QPushButton#btnDanger:hover {{
    background-color: #8c1a1a;
}}
QPushButton#btnSecondary {{
    background-color: {BG_WIDGET};
    color: {FG_PRIMARY};
    border: 1px solid {BORDER};
}}
QPushButton#btnSecondary:hover {{
    background-color: {BG_INPUT};
}}

/* プログレスバー */
QProgressBar {{
    background-color: {BG_WIDGET};
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: {FG_ACCENT};
    border-radius: 3px;
}}

/* スクロールバー */
QScrollBar:vertical {{
    background: {BG_PANEL};
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {SCROLLBAR};
    border-radius: 5px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: #686868;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {BG_PANEL};
    height: 10px;
}}
QScrollBar::handle:horizontal {{
    background: {SCROLLBAR};
    border-radius: 5px;
    min-width: 20px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* セパレータラベル */
QLabel#sectionLabel {{
    color: {FG_SECONDARY};
    font-size: 9pt;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 6px 8px 2px 8px;
}}

/* サイドバーメトリクスラベル */
QLabel#metricValue {{
    color: {FG_ACCENT};
    font-family: {FONT_MONO};
    font-size: {FONT_SIZE_UI}pt;
}}

/* ログパネル */
QPlainTextEdit#logPanel {{
    background-color: #0d0d0d;
    color: #cccccc;
    font-family: {FONT_MONO};
    font-size: 9pt;
    border-top: 1px solid {BORDER};
}}

/* ダイアログ */
QDialog {{
    background-color: {BG_PANEL};
}}
QDialog QLabel {{
    color: {FG_PRIMARY};
}}
"""