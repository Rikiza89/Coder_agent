

# =============================================================================
# agentic_coder/main.py
# =============================================================================
# エントリポイント — 依存関係の注入と起動シーケンスを管理する
# =============================================================================

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from .agents.coder import CoderAgent
from .agents.debugger import DebuggerAgent
from .agents.planner import PlannerAgent
from .agents.tester import TesterAgent
from .config import AppConfig
from .domain.exceptions import AgentError
from .infrastructure.code_runner import CodeRunner
from .infrastructure.embedder import OllamaEmbedder
from .infrastructure.llm_client import OllamaLLMClient
from .infrastructure.memory_store import MemoryStore
from .services.orchestrator import Orchestrator


def _configure_logging() -> None:
    """構造化ログを設定する — センシティブデータを含まない形式。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
    )


def build_orchestrator(config: AppConfig) -> Orchestrator:
    """
    依存関係を注入してOrchestratorインスタンスを構築するファクトリ関数。
    DIコンテナの役割を担い、全インフラ依存をここで解決する。

    Args:
        config: 検証済みアプリケーション設定

    Returns:
        使用可能なOrchestratorインスタンス
    """
    output_dir = Path(config.agent.output_dir)

    # インフラ層のインスタンス化
    llm = OllamaLLMClient(config.ollama)
    embedder = OllamaEmbedder(config.ollama)
    memory = MemoryStore(config.memory, embedder)
    runner = CodeRunner()

    # エージェント層のインスタンス化 — インフラ依存を注入
    planner = PlannerAgent(llm, memory)
    coder = CoderAgent(llm, output_dir)
    tester = TesterAgent(llm, output_dir)
    debugger = DebuggerAgent(llm)

    return Orchestrator(
        config=config.agent,
        planner=planner,
        coder=coder,
        tester=tester,
        debugger=debugger,
        runner=runner,
        memory=memory,
        output_dir=output_dir,
    )


def main() -> None:
    """
    メインエントリポイント。
    設定検証 → DI構築 → 目標入力 → オーケストレーション実行の順に処理する。
    """
    _configure_logging()
    logger = logging.getLogger(__name__)

    # 設定の構築と検証
    config = AppConfig()
    try:
        config.validate()
    except ValueError as exc:
        logger.critical("設定検証失敗: %s", exc)
        sys.exit(1)

    orchestrator = build_orchestrator(config)

    goal = input("プロジェクト目標を入力してください: ").strip()
    if not goal:
        logger.error("目標が空です。終了します。")
        sys.exit(1)

    start = time.monotonic()
    try:
        plan = orchestrator.run(goal)
        elapsed = time.monotonic() - start
        completed = sum(1 for t in plan.tasks if t.status.name == "COMPLETE")
        print(f"\n✓ プロジェクト完了: {completed}/{len(plan.tasks)} タスク成功 ({elapsed:.2f}秒)")
    except AgentError as exc:
        logger.error("エージェントエラーで処理終了: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()