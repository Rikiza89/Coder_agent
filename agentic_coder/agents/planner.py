
# =============================================================================
# agentic_coder/agents/planner.py
# =============================================================================
# 計画エージェント — プロジェクト目標をファイルタスクに分解する
# =============================================================================

from __future__ import annotations

import json
import logging
import re

from ..domain.exceptions import LLMCallError, PlanParseError
from ..domain.models import FileTask, ProjectPlan
from ..infrastructure.llm_client import LLMClientProtocol
from ..infrastructure.memory_store import MemoryStore

logger = logging.getLogger(__name__)

# JSONブロックを抽出する正規表現 — LLMが余分なテキストを含む場合の対策
_JSON_BLOCK_RE = re.compile(r"\[.*?\]", re.DOTALL)


class PlannerAgent:
    """
    自然言語目標をファイルタスクリストに分解するエージェント。

    Args:
        llm: LLMクライアント実装
        memory: メモリストア実装
    """

    def __init__(self, llm: LLMClientProtocol, memory: MemoryStore) -> None:
        self._llm = llm
        self._memory = memory

    def plan(self, goal: str) -> ProjectPlan:
        """
        プロジェクト目標から実行計画を生成する。

        Args:
            goal: ユーザーの自然言語プロジェクト目標

        Returns:
            ファイルタスクを含むProjectPlanインスタンス

        Raises:
            LLMCallError: LLM呼び出し失敗時
            PlanParseError: LLM応答のJSONパース失敗時
        """
        memory_context = self._memory.retrieve(goal)

        prompt = self._build_prompt(goal, memory_context)
        logger.info("計画生成開始 | goal=%s", goal[:80])

        raw_response = self._llm.generate(prompt)
        tasks = self._parse_plan(raw_response)

        logger.info("計画生成完了 | task_count=%d", len(tasks))
        return ProjectPlan(goal=goal, tasks=tasks)

    def _build_prompt(self, goal: str, memory_context: str) -> str:
        """計画生成プロンプトを構築する。"""
        return f"""You are a senior software architect.

Break this project into Python files. Each file should be a focused, single-responsibility module.

Return ONLY a valid JSON array with no markdown, no explanation:
[
  {{"file": "filename.py", "description": "clear description of this file's responsibility"}}
]

Project goal:
{goal}

Relevant past context:
{memory_context if memory_context else "None"}
"""

    def _parse_plan(self, raw: str) -> list[FileTask]:
        """
        LLM応答からJSONを抽出してFileTaskリストに変換する。

        Args:
            raw: LLMの生応答テキスト

        Returns:
            FileTaskのリスト

        Raises:
            PlanParseError: JSON抽出またはパース失敗時
        """
        match = _JSON_BLOCK_RE.search(raw)
        if not match:
            raise PlanParseError(f"LLM応答にJSONリストが見つからない: {raw[:200]}")

        try:
            data = json.loads(match.group())
        except json.JSONDecodeError as exc:
            raise PlanParseError(f"計画JSONのパース失敗: {exc}") from exc

        if not isinstance(data, list) or not data:
            raise PlanParseError("計画は空でないリストでなければならない")

        tasks: list[FileTask] = []
        for item in data:
            if "file" not in item or "description" not in item:
                raise PlanParseError(f"タスク項目に必須フィールドが不足: {item}")
            tasks.append(FileTask(file=item["file"], description=item["description"]))

        return tasks