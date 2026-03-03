
# =============================================================================
# agentic_coder/agents/tester.py
# =============================================================================
# テスト生成エージェント — pytestテストコードを自動生成する
# =============================================================================

from __future__ import annotations

import logging
from pathlib import Path

from ..domain.exceptions import LLMCallError
from ..domain.models import FileTask, TaskStatus
from ..infrastructure.llm_client import LLMClientProtocol

logger = logging.getLogger(__name__)


class TesterAgent:
    """
    ソースファイルに対応するpytestテストを生成するエージェント。

    Args:
        llm: LLMクライアント実装
        output_dir: テストファイルの保存ディレクトリ
    """

    def __init__(self, llm: LLMClientProtocol, output_dir: Path) -> None:
        self._llm = llm
        self._output_dir = output_dir

    def generate_tests(self, task: FileTask, source_path: Path) -> Path:
        """
        ソースファイルに対応するpytestテストファイルを生成・保存する。

        Args:
            task: テスト対象のファイルタスク
            source_path: テスト対象ソースファイルのパス

        Returns:
            生成されたテストファイルのPath

        Raises:
            LLMCallError: LLM呼び出し失敗時
        """
        task.status = TaskStatus.TESTING
        code = source_path.read_text(encoding="utf-8")
        logger.info("テスト生成開始 | source=%s", source_path)

        prompt = self._build_prompt(task.file, code)
        raw = self._llm.generate(prompt)
        test_code = self._extract_code(raw)

        test_path = self._output_dir / f"test_{task.file}"
        test_path.write_text(test_code, encoding="utf-8")

        logger.info("テスト保存完了 | path=%s", test_path)
        return test_path

    def _build_prompt(self, filename: str, code: str) -> str:
        """テスト生成プロンプトを構築する。"""
        return f"""Write complete pytest unit tests for this Python module: {filename}

Requirements:
- Test all public functions and classes
- Include edge cases and error cases
- Use pytest fixtures where appropriate
- Mock external dependencies
- Tests must be runnable independently

Source code:
{code}

Return ONLY valid pytest code. No markdown, no explanation.
"""

    def _extract_code(self, raw: str) -> str:
        """LLM応答からコードフェンスを除去する。"""
        lines = raw.strip().splitlines()
        if lines and (lines[0].startswith("```") or lines[0].startswith("~~~")):
            lines = lines[1:]
        if lines and lines[-1].strip() in ("```", "~~~"):
            lines = lines[:-1]
        return "\n".join(lines)