
# =============================================================================
# agentic_coder/ui/main_window.py
# =============================================================================
# メインウィンドウ — 全UIコンポーネントを統合するエントリポイント
# =============================================================================

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QAction, QFont, QIcon, QKeySequence
from PySide6.QtWidgets import (QApplication, QDialog, QFileDialog,
                                QHBoxLayout, QLabel, QMainWindow,
                                QMessageBox, QPlainTextEdit, QProgressBar,
                                QPushButton, QSizePolicy, QSplitter,
                                QStatusBar, QTextEdit, QToolBar,
                                QVBoxLayout, QWidget)

from . import theme
from .code_canvas import CodeCanvas
from .file_tree import FileTreePanel
from .log_panel import LogPanel
from .sidebar import SidebarPanel
from .workers import AgentWorker


class RequestPanel(QWidget):
    """
    ユーザー入力エリア — プロジェクト目標テキストと実行ボタンを提供する。
    """

    def __init__(self) -> None:
        super().__init__()
        self.setFixedHeight(110)
        self.setStyleSheet(f"background:{theme.BG_PANEL}; border-bottom:1px solid {theme.BORDER};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        top = QHBoxLayout()
        lbl = QLabel("Project Goal")
        lbl.setStyleSheet(f"color:{theme.FG_SECONDARY}; font-size:9pt;")

        self.btn_folder = QPushButton("📁 Work Folder")
        self.btn_folder.setObjectName("btnSecondary")
        self.btn_folder.setFixedHeight(24)

        self.btn_run = QPushButton("▶  Run Agent")
        self.btn_run.setFixedHeight(24)

        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.setObjectName("btnDanger")
        self.btn_stop.setFixedHeight(24)
        self.btn_stop.setEnabled(False)

        top.addWidget(lbl)
        top.addStretch()
        top.addWidget(self.btn_folder)
        top.addWidget(self.btn_run)
        top.addWidget(self.btn_stop)
        layout.addLayout(top)

        self.text_input = QTextEdit()
        self.text_input.setObjectName("requestInput")
        self.text_input.setPlaceholderText(
            "Describe your project goal… e.g. 'Build a REST API for a todo app with SQLite'"
        )
        self.text_input.setFixedHeight(56)
        layout.addWidget(self.text_input)

    def get_goal(self) -> str:
        """入力されたプロジェクト目標テキストを返す。"""
        return self.text_input.toPlainText().strip()

    def set_running(self, running: bool) -> None:
        """実行状態に応じてボタンの有効/無効を切り替える。"""
        self.btn_run.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        self.text_input.setReadOnly(running)


class MainWindow(QMainWindow):
    """
    アプリケーションメインウィンドウ。
    メニューバー、ツールバー、スプリッターレイアウト、
    ステータスバーを統合する。

    Args:
        orchestrator_factory: AppConfigを受け取りOrchestratorを返すファクトリ関数
    """

    def __init__(self, orchestrator_factory) -> None:
        super().__init__()
        self._orchestrator_factory = orchestrator_factory
        self._work_dir = Path.cwd() / "output"
        self._worker: AgentWorker | None = None
        self._thread: QThread | None = None
        self._task_done = 0
        self._task_total = 0

        self.setWindowTitle("Agentic Coder")
        self.resize(1400, 900)
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self.set_status("Ready")

    # ------------------------------------------------------------------
    # UI構築
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        """メインレイアウトを構築する。"""
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # リクエストパネル (上部固定)
        self._request = RequestPanel()
        self._request.btn_run.clicked.connect(self._on_run)
        self._request.btn_stop.clicked.connect(self._on_stop)
        self._request.btn_folder.clicked.connect(self._on_select_folder)
        root.addWidget(self._request)

        # メインコンテンツ — 水平スプリッター
        h_split = QSplitter(Qt.Horizontal)
        h_split.setHandleWidth(2)

        # 左: ファイルツリー
        self._file_tree = FileTreePanel()
        h_split.addWidget(self._file_tree)

        # 中央: コードキャンバス (メイン)
        self._canvas = CodeCanvas(self._work_dir)

        # 右: サイドバー
        self._sidebar = SidebarPanel()

        # 中央コンテンツ + 垂直ログスプリッター
        v_split = QSplitter(Qt.Vertical)
        v_split.addWidget(self._canvas)
        self._log_panel = LogPanel()
        v_split.addWidget(self._log_panel)
        v_split.setSizes([600, 200])

        h_split.addWidget(v_split)
        h_split.addWidget(self._sidebar)
        h_split.setSizes([200, 980, 220])

        root.addWidget(h_split)

    def _setup_menu(self) -> None:
        """メニューバーを構築する。"""
        mb = self.menuBar()

        # File メニュー
        m_file = mb.addMenu("&File")
        a_folder = QAction("📁 Set Work Folder…", self)
        a_folder.setShortcut(QKeySequence("Ctrl+Shift+O"))
        a_folder.triggered.connect(self._on_select_folder)
        m_file.addAction(a_folder)
        m_file.addSeparator()
        a_quit = QAction("Quit", self)
        a_quit.setShortcut(QKeySequence("Ctrl+Q"))
        a_quit.triggered.connect(QApplication.quit)
        m_file.addAction(a_quit)

        # Agent メニュー
        m_agent = mb.addMenu("&Agent")
        a_run = QAction("▶  Run Agent", self)
        a_run.setShortcut(QKeySequence("F5"))
        a_run.triggered.connect(self._on_run)
        m_agent.addAction(a_run)
        a_stop = QAction("⏹  Stop Agent", self)
        a_stop.setShortcut(QKeySequence("F6"))
        a_stop.triggered.connect(self._on_stop)
        m_agent.addAction(a_stop)
        m_agent.addSeparator()
        a_clear = QAction("🗑  Clear Tree & Canvas", self)
        a_clear.triggered.connect(self._on_clear)
        m_agent.addAction(a_clear)

        # View メニュー
        m_view = mb.addMenu("&View")
        a_log = QAction("Toggle Log Panel", self)
        a_log.setShortcut(QKeySequence("Ctrl+`"))
        a_log.triggered.connect(
            lambda: self._log_panel.setVisible(not self._log_panel.isVisible())
        )
        m_view.addAction(a_log)

        # Config メニュー
        m_cfg = mb.addMenu("&Config")
        a_env = QAction("⚙  Edit Environment…", self)
        a_env.triggered.connect(self._on_edit_env)
        m_cfg.addAction(a_env)

        # Help メニュー
        m_help = mb.addMenu("&Help")
        a_about = QAction("About Agentic Coder", self)
        a_about.triggered.connect(self._on_about)
        m_help.addAction(a_about)

    def _setup_toolbar(self) -> None:
        """クイックアクセスツールバーを構築する。"""
        tb = QToolBar("Main Toolbar")
        tb.setMovable(False)
        self.addToolBar(tb)

        for text, tip, slot in [
            ("📁 Folder", "Set work folder (Ctrl+Shift+O)", self._on_select_folder),
            ("▶ Run",    "Run agent (F5)",                 self._on_run),
            ("⏹ Stop",   "Stop agent (F6)",                self._on_stop),
            ("🗑 Clear",  "Clear tree & canvas",            self._on_clear),
        ]:
            btn = tb.addWidget(self._make_tb_btn(text, tip, slot))

        tb.addSeparator()
        # 進捗バー — ツールバー右端
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setFixedWidth(160)
        self._progress.setFixedHeight(14)
        self._progress.setValue(0)
        tb.addWidget(self._progress)

    def _make_tb_btn(self, text: str, tip: str, slot) -> QPushButton:
        """ツールバー用ボタンを生成する。"""
        btn = QPushButton(text)
        btn.setToolTip(tip)
        btn.setObjectName("btnSecondary")
        btn.setFixedHeight(26)
        btn.clicked.connect(slot)
        return btn

    def _setup_statusbar(self) -> None:
        """ステータスバーを構築する。"""
        sb = QStatusBar()
        self.setStatusBar(sb)

        self._status_lbl = QLabel("Ready")
        self._folder_lbl = QLabel(f"📁 {self._work_dir}")
        self._folder_lbl.setStyleSheet("color:rgba(255,255,255,0.7); font-size:9pt;")

        sb.addWidget(self._status_lbl)
        sb.addPermanentWidget(self._folder_lbl)

    # ------------------------------------------------------------------
    # スロット / イベントハンドラ
    # ------------------------------------------------------------------

    def set_status(self, msg: str) -> None:
        """ステータスバーとサイドバーのステータスを同時更新する。"""
        self._status_lbl.setText(msg)

    def _on_select_folder(self) -> None:
        """作業ディレクトリを選択または新規作成する。"""
        path = QFileDialog.getExistingDirectory(
            self, "Select or Create Work Folder",
            str(self._work_dir),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if path:
            self._work_dir = Path(path)
            self._work_dir.mkdir(parents=True, exist_ok=True)
            self._canvas.set_output_dir(self._work_dir)
            self._folder_lbl.setText(f"📁 {self._work_dir}")
            self.set_status(f"Work folder: {self._work_dir}")

    def _on_run(self) -> None:
        """エージェントを起動する。"""
        goal = self._request.get_goal()
        if not goal:
            QMessageBox.warning(self, "Input Required", "Please enter a project goal.")
            return

        if self._thread and self._thread.isRunning():
            QMessageBox.information(self, "Running", "Agent is already running.")
            return

        self._work_dir.mkdir(parents=True, exist_ok=True)
        self._file_tree.clear_all()
        self._task_done = 0
        self._task_total = 0
        self._progress.setValue(0)
        self._sidebar.set_project_info(goal, str(self._work_dir))

        # オーケストレーター生成 — 作業ディレクトリを反映した設定で
        try:
            from ..config import AppConfig, AgentConfig, OllamaConfig, MemoryConfig
            import dataclasses
            cfg = AppConfig(
                agent=AgentConfig(output_dir=str(self._work_dir))
            )
            cfg.validate()
            orchestrator = self._orchestrator_factory(cfg)
        except Exception as exc:
            QMessageBox.critical(self, "Config Error", str(exc))
            return

        self._worker = AgentWorker(orchestrator, goal)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)

        # シグナル接続 — クロススレッドUI更新
        self._thread.started.connect(self._worker.run)
        self._worker.log_message.connect(self._log_panel.append)
        self._worker.file_started.connect(self._on_file_started)
        self._worker.file_complete.connect(self._on_file_complete)
        self._worker.file_failed.connect(self._on_file_failed)
        self._worker.code_ready.connect(self._on_code_ready)
        self._worker.progress.connect(self._progress.setValue)
        self._worker.finished.connect(self._on_agent_finished)
        self._worker.error.connect(self._on_agent_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)

        self._request.set_running(True)
        self.set_status("🤖 Agent running…")
        self._thread.start()

    def _on_stop(self) -> None:
        """エージェントスレッドを安全に停止する。"""
        if self._thread and self._thread.isRunning():
            self._thread.requestInterruption()
            self._thread.quit()
            self._thread.wait(3000)
            self.set_status("⏹ Stopped by user")
            self._request.set_running(False)

    def _on_clear(self) -> None:
        """ツリーとキャンバスをリセットする。"""
        self._file_tree.clear_all()
        while self._canvas.count():
            self._canvas.removeTab(0)
        self._canvas._tabs.clear()
        self._progress.setValue(0)
        self.set_status("Cleared")

    def _on_file_started(self, filename: str) -> None:
        """ファイル生成開始時のUI更新。"""
        self._file_tree.add_file(filename)
        self._file_tree.set_status(filename, "coding")
        self._task_total += 1
        self._sidebar.set_task_progress(self._task_done, self._task_total)
        self.set_status(f"⚙ Generating {filename}…")

    def _on_file_complete(self, filename: str) -> None:
        """ファイル生成完了時のUI更新。"""
        self._file_tree.set_status(filename, "complete")
        self._task_done += 1
        self._sidebar.set_task_progress(self._task_done, self._task_total)
        self.set_status(f"✅ {filename} complete")

    def _on_file_failed(self, filename: str, error: str) -> None:
        """ファイル生成失敗時のUI更新。"""
        self._file_tree.set_status(filename, "failed")
        self._log_panel.append(f"[ERROR] {filename}: {error}")
        self.set_status(f"❌ {filename} failed")

    def _on_code_ready(self, filename: str, code: str,
                       is_fix: bool, old_code: str) -> None:
        """生成コードをキャンバスに追加/更新する。"""
        self._canvas.upsert_file(filename, code, is_fix, old_code)
        if is_fix:
            self._file_tree.set_status(filename, "debugging")

    def _on_agent_finished(self) -> None:
        """エージェント正常終了時の処理。"""
        self._request.set_running(False)
        self.set_status(
            f"✅ Done — {self._task_done}/{self._task_total} files generated"
        )
        self._progress.setValue(100)

    def _on_agent_error(self, msg: str) -> None:
        """エージェント致命的エラー時の処理。"""
        self._request.set_running(False)
        self.set_status(f"❌ Error: {msg}")
        QMessageBox.critical(self, "Agent Error", msg)

    def _on_edit_env(self) -> None:
        """環境変数編集ダイアログを表示する。"""
        env_vars = [
            "OLLAMA_URL", "OLLAMA_MODEL", "OLLAMA_EMBED_MODEL",
            "OLLAMA_TIMEOUT", "MAX_DEBUG_RETRIES", "OUTPUT_DIR",
        ]
        dlg = QDialog(self)
        dlg.setWindowTitle("Environment Configuration")
        dlg.resize(500, 380)
        layout = QVBoxLayout(dlg)

        from PySide6.QtWidgets import QFormLayout, QLineEdit, QDialogButtonBox
        form = QFormLayout()
        editors: dict[str, QLineEdit] = {}
        for var in env_vars:
            le = QLineEdit(os.environ.get(var, ""))
            le.setPlaceholderText(f"default")
            form.addRow(QLabel(var), le)
            editors[var] = le

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec() == QDialog.Accepted:
            for var, le in editors.items():
                val = le.text().strip()
                if val:
                    os.environ[var] = val
                elif var in os.environ:
                    del os.environ[var]
            self.set_status("Environment updated")

    def _on_about(self) -> None:
        """Aboutダイアログを表示する。"""
        QMessageBox.about(
            self, "Agentic Coder",
            "<b>Agentic Coder</b><br>"
            "Local AI-powered Python project generator<br><br>"
            "Backend: Ollama (local LLM)<br>"
            "UI: PySide6<br>"
            "Architecture: Clean Architecture + QThread",
        )
