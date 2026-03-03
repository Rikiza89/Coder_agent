
# =============================================================================
# agentic_coder/ui/workers.py
# =============================================================================
# QThreadワーカー — UIスレッドをブロックせずエージェントを実行する
# シグナル経由でのみUIを更新 — スレッド安全性を保証
# =============================================================================

from __future__ import annotations

import logging
import traceback
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

logger = logging.getLogger(__name__)


class LogSignalHandler(logging.Handler):
    """
    Pythonロギングシステムをシグナルにブリッジするハンドラ。
    バックエンドの全ログをUIのログパネルにリアルタイム転送する。

    Args:
        signal: ログメッセージを送出するQt Signal
    """

    def __init__(self, signal: Signal) -> None:
        super().__init__()
        self._signal = signal
        self.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                              datefmt="%H:%M:%S")
        )

    def emit(self, record: logging.LogRecord) -> None:
        """ログレコードをフォーマットしてシグナルとして送出する。"""
        try:
            msg = self.format(record)
            self._signal.emit(msg)
        except Exception:
            # ログハンドラ内での例外は握りつぶす — 再帰的エラーを防ぐ
            pass


class AgentWorker(QObject):
    """
    エージェントオーケストレーションをバックグラウンドスレッドで実行するワーカー。

    シグナル:
        log_message: ログ文字列をUIに転送
        file_started: ファイル生成開始通知 (filename)
        file_complete: ファイル生成完了通知 (filename)
        file_failed: ファイル生成失敗通知 (filename, error)
        code_ready: 生成コードをUIに転送 (filename, code, is_fix, old_code)
        progress: 進捗率 (0-100)
        finished: 全処理完了通知
        error: 致命的エラー通知 (message)
    """

    log_message  = Signal(str)
    file_started = Signal(str)
    file_complete = Signal(str)
    file_failed  = Signal(str, str)
    code_ready   = Signal(str, str, bool, str)  # file, code, is_fix, old_code
    progress     = Signal(int)
    finished     = Signal()
    error        = Signal(str)

    def __init__(self, orchestrator, goal: str) -> None:
        super().__init__()
        self._orchestrator = orchestrator
        self._goal = goal
        self._log_handler: LogSignalHandler | None = None

    def run(self) -> None:
        """
        エージェントを実行するメインワーカーメソッド。
        QThread.start()から呼び出される。
        """
        # Pythonロガーをシグナルにブリッジ
        self._log_handler = LogSignalHandler(self.log_message)
        root_logger = logging.getLogger()
        root_logger.addHandler(self._log_handler)
        root_logger.setLevel(logging.DEBUG)

        try:
            # オーケストレーターにコールバックを注入して進捗を報告
            self._run_with_callbacks()
            self.finished.emit()
        except Exception as exc:
            tb = traceback.format_exc()
            logger.error("ワーカー致命的エラー: %s\n%s", exc, tb)
            self.error.emit(str(exc))
        finally:
            if self._log_handler:
                root_logger.removeHandler(self._log_handler)

    def _run_with_callbacks(self) -> None:
        """
        オーケストレーターにモンキーパッチを適用してUIコールバックを注入する。
        実行フックなしのオーケストレーターAPIとの後方互換性を維持する。
        """
        from ..services.orchestrator import Orchestrator
        orig_run = self._orchestrator.run

        # タスクカウントを取得するため計画のみ先行実行
        plan = self._orchestrator._planner.plan(self._goal)
        total = len(plan.tasks)

        for i, task in enumerate(plan.tasks):
            self.file_started.emit(task.file)
            self.progress.emit(int((i / total) * 100))

            try:
                # コーダー実行
                source_path = self._orchestrator._coder.code(task)
                old_code = ""

                # テスト生成
                self._orchestrator._tester.generate_tests(task, source_path)

                # 検証ループ
                from ..config import AgentConfig
                max_retries = self._orchestrator._config.max_debug_retries
                for attempt in range(1, max_retries + 1):
                    passed, output = self._orchestrator._runner.run_tests(
                        self._orchestrator._output_dir
                    )
                    current_code = source_path.read_text(encoding="utf-8")

                    if passed:
                        self.code_ready.emit(task.file, current_code, False, "")
                        self.file_complete.emit(task.file)
                        self._orchestrator._memory.add(
                            f"成功: {task.file} — {task.description}"
                        )
                        break

                    if attempt < max_retries:
                        old_code = current_code
                        self._orchestrator._debugger.fix(task, source_path, output)
                        new_code = source_path.read_text(encoding="utf-8")
                        # diff付きコードをUIに送信
                        self.code_ready.emit(task.file, new_code, True, old_code)
                    else:
                        self.file_failed.emit(task.file, output)
                        self._orchestrator._memory.add(
                            f"失敗: {task.file} — デバッグ上限超過"
                        )

            except Exception as exc:
                self.file_failed.emit(task.file, str(exc))
                logger.error("タスク処理エラー | file=%s | error=%s", task.file, exc)

        self.progress.emit(100)
        self._orchestrator._memory.add(f"プロジェクト完了: {self._goal}")

