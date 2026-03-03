
# =============================================================================
# agentic_coder/agents/debugger.py
# =============================================================================
# デバッグエージェント — テスト失敗を解析しコードを自動修正する
# =============================================================================

from __future__ import annotations

import logging
from pathlib import Path

from ..domain.exceptions import LLMCallError
from ..domain.models import FileTask, TaskStatus
from ..infrastructure.llm_client import LLMClientProtocol

logger = logging.getLogger(__name__)


class DebuggerAgent:
    """
    テスト失敗を受けてソースコードを自動修正するエージェント。

    Args:
        llm: LLMクライアント実装
    """

    def __init__(self, llm: LLMClientProtocol) -> None:
        self._llm = llm

    def fix(self, task: FileTask, source_path: Path, error_output: str) -> None:
        """
        エラー出力に基づいてソースファイルをインプレース修正する。

        Args:
            task: デバッグ対象のファイルタスク
            source_path: 修正対象ソースファイルのパス
            error_output: pytestのエラー出力テキスト

        Raises:
            LLMCallError: LLM呼び出し失敗時
        """
        task.status = TaskStatus.DEBUGGING
        task.attempt_count += 1
        task.error_log = error_output

        current_code = source_path.read_text(encoding="utf-8")
        logger.info(
            "デバッグ試行 | file=%s | attempt=%d",
            source_path.name,
            task.attempt_count,
        )

        prompt = self._build_prompt(source_path.name, current_code, error_output)
        raw = self._llm.generate(prompt)
        fixed_code = self._extract_code(raw)

        source_path.write_text(fixed_code, encoding="utf-8")
        logger.info("修正コード保存 | path=%s", source_path)

    def _build_prompt(self, filename: str, code: str, error: str) -> str:
        """デバッグプロンプトを構築する。"""
        return f"""You are debugging a Python file. Fix the code so all tests pass.

File: {filename}

Current code:
{code}

Test failure output:
{error}

Return ONLY the complete fixed Python code. No markdown, no explanation.
"""

    def _extract_code(self, raw: str) -> str:
        """LLM応答からコードフェンスを除去する。"""
        lines = raw.strip().splitlines()
        if lines and (lines[0].startswith("```") or lines[0].startswith("~~~")):
            lines = lines[1:]
        if lines and lines[-1].strip() in ("```", "~~~"):
            lines = lines[:-1]
        return "\n".join(lines)