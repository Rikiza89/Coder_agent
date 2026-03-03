
# =============================================================================
# agentic_coder/ui/sidebar.py
# =============================================================================
# サイドバー — メタデータとハードウェアメトリクスを表示する
# psutilとGPU情報をポーリングして定期更新する
# =============================================================================

from __future__ import annotations

import platform
import subprocess
from typing import Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (QFrame, QLabel, QProgressBar,
                                QVBoxLayout, QWidget)

from . import theme

try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    _PSUTIL_AVAILABLE = False


def _get_gpu_usage() -> Optional[tuple[float, float]]:
    """
    GPU使用率とVRAM使用率を取得する。
    nvidia-smiが利用可能な場合のみ動作する。

    Returns:
        (gpu_percent, vram_percent) のタプル、取得不可の場合はNone
    """
    try:
        out = subprocess.check_output(
            ["nvidia-smi",
             "--query-gpu=utilization.gpu,memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            timeout=2, stderr=subprocess.DEVNULL
        ).decode()
        parts = [p.strip() for p in out.strip().split(",")]
        gpu_pct = float(parts[0])
        vram_pct = float(parts[1]) / float(parts[2]) * 100
        return gpu_pct, vram_pct
    except Exception:
        return None


def _get_ollama_model() -> str:
    """
    現在Ollamaにロードされているモデル名を取得する。

    Returns:
        モデル名文字列、取得失敗時は'—'
    """
    try:
        out = subprocess.check_output(
            ["ollama", "ps"], timeout=2, stderr=subprocess.DEVNULL
        ).decode()
        lines = [l for l in out.strip().splitlines() if l and not l.startswith("NAME")]
        return lines[0].split()[0] if lines else "—"
    except Exception:
        return "—"


class MetricRow(QWidget):
    """
    ラベル + プログレスバー + 値テキストの単一メトリクス行。

    Args:
        label: メトリクス名
        color: プログレスバーの色
    """

    def __init__(self, label: str, color: str = theme.FG_ACCENT) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)

        self._lbl = QLabel(label)
        self._lbl.setStyleSheet(f"color:{theme.FG_SECONDARY}; font-size:9pt;")

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setFixedHeight(6)
        self._bar.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {color}; border-radius:3px; }}"
        )

        self._val = QLabel("—")
        self._val.setObjectName("metricValue")

        layout.addWidget(self._lbl)
        layout.addWidget(self._bar)
        layout.addWidget(self._val)

    def update(self, percent: float, text: str) -> None:
        """メトリクス値を更新する。"""
        self._bar.setValue(int(percent))
        self._val.setText(text)


class SidebarPanel(QWidget):
    """
    プロジェクトメタデータとハードウェア使用率を表示するサイドバー。
    タイマーによる定期ポーリングでメトリクスをリアルタイム更新する。
    """

    # メトリクス更新間隔 (ms) — 頻繁すぎると負荷になる
    _POLL_INTERVAL_MS = 2000

    def __init__(self) -> None:
        super().__init__()
        self.setFixedWidth(220)
        self._setup_ui()
        self._start_polling()

    def _section(self, title: str) -> QLabel:
        """セクションヘッダーラベルを生成する。"""
        lbl = QLabel(title.upper())
        lbl.setObjectName("sectionLabel")
        return lbl

    def _divider(self) -> QFrame:
        """水平区切り線を生成する。"""
        f = QFrame()
        f.setFrameShape(QFrame.HLine)
        f.setStyleSheet(f"color:{theme.BORDER};")
        return f

    def _setup_ui(self) -> None:
        """サイドバーUIを構築する。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(0)

        # プロジェクト情報セクション
        layout.addWidget(self._section("Project"))
        self._lbl_goal = QLabel("—")
        self._lbl_goal.setWordWrap(True)
        self._lbl_goal.setStyleSheet(f"color:{theme.FG_PRIMARY}; padding:4px 8px; font-size:9pt;")
        self._lbl_work_dir = QLabel("—")
        self._lbl_work_dir.setWordWrap(True)
        self._lbl_work_dir.setStyleSheet(f"color:{theme.FG_SECONDARY}; padding:2px 8px; font-size:8pt;")
        self._lbl_tasks = QLabel("Tasks: 0 / 0")
        self._lbl_tasks.setStyleSheet(f"color:{theme.FG_ACCENT}; padding:2px 8px; font-size:9pt;")
        layout.addWidget(self._lbl_goal)
        layout.addWidget(self._lbl_work_dir)
        layout.addWidget(self._lbl_tasks)
        layout.addWidget(self._divider())

        # ハードウェアセクション
        layout.addWidget(self._section("Hardware"))
        self._cpu_row = MetricRow("CPU", theme.FG_ACCENT)
        self._ram_row = MetricRow("RAM", theme.FG_SUCCESS)
        self._gpu_row = MetricRow("GPU", "#c586c0")
        self._vram_row = MetricRow("VRAM", theme.FG_WARNING)
        layout.addWidget(self._cpu_row)
        layout.addWidget(self._ram_row)
        layout.addWidget(self._gpu_row)
        layout.addWidget(self._vram_row)
        layout.addWidget(self._divider())

        # Ollamaモデルセクション
        layout.addWidget(self._section("Ollama"))
        self._lbl_model = QLabel("—")
        self._lbl_model.setObjectName("metricValue")
        self._lbl_model.setStyleSheet(
            f"color:{theme.FG_ACCENT}; padding:4px 8px; font-size:9pt; font-family:Consolas;"
        )
        self._lbl_model.setWordWrap(True)
        layout.addWidget(self._lbl_model)

        layout.addStretch()

        if not _PSUTIL_AVAILABLE:
            warn = QLabel("⚠ psutil未インストール\npip install psutil")
            warn.setStyleSheet(f"color:{theme.FG_WARNING}; padding:8px; font-size:8pt;")
            layout.addWidget(warn)

    def _start_polling(self) -> None:
        """定期メトリクス更新タイマーを起動する。"""
        self._timer = QTimer(self)
        self._timer.setInterval(self._POLL_INTERVAL_MS)
        self._timer.timeout.connect(self._refresh_metrics)
        self._timer.start()
        self._refresh_metrics()  # 即時初回更新

    def _refresh_metrics(self) -> None:
        """ハードウェアメトリクスを更新する — UIスレッドで実行。"""
        if _PSUTIL_AVAILABLE:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            self._cpu_row.update(cpu, f"{cpu:.1f}%")
            ram_pct = mem.percent
            ram_gb = mem.used / 1024 ** 3
            self._ram_row.update(ram_pct, f"{ram_gb:.1f} GB ({ram_pct:.0f}%)")
        else:
            self._cpu_row.update(0, "N/A")
            self._ram_row.update(0, "N/A")

        gpu = _get_gpu_usage()
        if gpu:
            self._gpu_row.update(gpu[0], f"{gpu[0]:.1f}%")
            self._vram_row.update(gpu[1], f"{gpu[1]:.1f}%")
        else:
            self._gpu_row.update(0, "N/A")
            self._vram_row.update(0, "N/A")

        model = _get_ollama_model()
        self._lbl_model.setText(model)

    def set_project_info(self, goal: str, work_dir: str) -> None:
        """プロジェクト情報ラベルを更新する。"""
        # 長いゴールは省略表示
        short_goal = goal[:60] + "…" if len(goal) > 60 else goal
        self._lbl_goal.setText(short_goal)
        self._lbl_goal.setToolTip(goal)
        self._lbl_work_dir.setText(work_dir)

    def set_task_progress(self, done: int, total: int) -> None:
        """タスク進捗カウンターを更新する。"""
        self._lbl_tasks.setText(f"Tasks: {done} / {total}")
