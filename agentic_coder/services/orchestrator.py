
# =============================================================================
# agentic_coder/services/orchestrator.py
# =============================================================================
# オーケストレーターサービス — エージェント間の協調を管理するアプリケーション層
# ビジネスロジックはエージェント内に留め、ここではフローのみを制御する
# =============================================================================

from __future__ import annotations

import logging
import time
from pathlib import Path

from ..agents.coder import CoderAgent
from ..agents.debugger import DebuggerAgent
from ..agents.planner import PlannerAgent
from ..agents.tester import TesterAgent
from ..config import AgentConfig
from ..domain.exceptions import MaxRetriesExceededError, PlanParseError
from ..domain.models import ProjectPlan, TaskStatus
from ..infrastructure.code_runner import CodeRunner
from ..infrastructure.memory_store import MemoryStore

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    プロジェクト全体のエージェント協調を管理するサービスクラス。

    責務:
    - 計画 → コーディング → テスト → デバッグのライフサイクル管理
    - 成功・失敗のメモリ記録
    - 最大リトライ数の強制

    Args:
        config: エージェント設定
        planner: 計画エージェント
        coder: コーダーエージェント
        tester: テスト生成エージェント
        debugger: デバッグエージェント
        runner: コード実行インフラ
        memory: メモリストア
        output_dir: 出力ディレクトリ
    """

    def __init__(
        self,
        config: AgentConfig,
        planner: PlannerAgent,
        coder: CoderAgent,
        tester: TesterAgent,
        debugger: DebuggerAgent,
        runner: CodeRunner,
        memory: MemoryStore,
        output_dir: Path,
    ) -> None:
        self._config = config
        self._planner = planner
        self._coder = coder
        self._tester = tester
        self._debugger = debugger
        self._runner = runner
        self._memory = memory
        self._output_dir = output_dir

    def run(self, goal: str) -> ProjectPlan:
        """
        プロジェクト目標を受け取り完全なプロジェクトを生成する。

        Args:
            goal: ユーザーの自然言語プロジェクト目標

        Returns:
            全タスクの最終状態を含むProjectPlan

        Raises:
            PlanParseError: 計画生成失敗時
            MaxRetriesExceededError: デバッグ上限超過時
        """
        start_time = time.monotonic()
        logger.info("オーケストレーション開始 | goal=%s", goal[:80])

        plan = self._planner.plan(goal)
        logger.info("計画生成完了 | tasks=%d", len(plan.tasks))

        for task in plan.tasks:
            logger.info("タスク処理開始 | file=%s", task.file)

            # コード生成
            source_path = self._coder.code(task)

            # テスト生成
            self._tester.generate_tests(task, source_path)

            # 検証ループ — 最大リトライ回数まで自動デバッグ
            passed = False
            for attempt in range(1, self._config.max_debug_retries + 1):
                logger.info("テスト実行 | file=%s | attempt=%d", task.file, attempt)
                passed, output = self._runner.run_tests(self._output_dir)

                if passed:
                    task.status = TaskStatus.COMPLETE
                    self._memory.add(f"成功: {task.file} — {task.description}")
                    logger.info("タスク完了 | file=%s", task.file)
                    break

                logger.warning("テスト失敗 | file=%s | attempt=%d", task.file, attempt)

                if attempt < self._config.max_debug_retries:
                    self._debugger.fix(task, source_path, output)
                else:
                    # 最大試行回数に達した — 失敗を記録して例外を送出
                    task.status = TaskStatus.FAILED
                    self._memory.add(f"失敗: {task.file} — デバッグ上限超過")
                    raise MaxRetriesExceededError(task.file, self._config.max_debug_retries)

        elapsed = time.monotonic() - start_time
        self._memory.add(f"プロジェクト完了: {goal}")
        logger.info("オーケストレーション完了 | elapsed=%.2fs", elapsed)

        return plan