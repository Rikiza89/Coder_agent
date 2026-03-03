
# =============================================================================
# agentic_coder/agents/coder.py
# =============================================================================
# コーダーエージェント — ファイルタスクからPythonコードを生成・保存する
# =============================================================================

from __future__ import annotations

import logging
from pathlib import Path

from ..domain.exceptions import LLMCallError
from ..domain.models import FileTask, TaskStatus
from ..infrastructure.llm_client import LLMClientProtocol

logger = logging.getLogger(__name__)

# LLM応答からコードブロックを除去するためのマーカー
_CODE_FENCE_MARKERS = ("```python", "```py", "```", "~~~")


class CoderAgent:
    """
    ファイルタスクの説明からPythonコードを生成するエージェント。

    Args:
        llm: LLMクライアント実装
        output_dir: 生成ファイルの保存ディレクトリ
    """

    def __init__(self, llm: LLMClientProtocol, output_dir: Path) -> None:
        self._llm = llm
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def code(self, task: FileTask) -> Path:
        """
        タスクに基づいてPythonファイルを生成・保存する。

        Args:
            task: 生成対象ファイルタスク

        Returns:
            保存されたファイルのPath

        Raises:
            LLMCallError: LLM呼び出し失敗時
        """
        task.status = TaskStatus.CODING
        logger.info("コード生成開始 | file=%s", task.file)

        prompt = self._build_prompt(task)
        raw = self._llm.generate(prompt)
        code = self._extract_code(raw)

        filepath = self._output_dir / task.file
        filepath.write_text(code, encoding="utf-8")

        logger.info("コード保存完了 | path=%s | lines=%d", filepath, code.count("\n"))
        return filepath

    def _build_prompt(self, task: FileTask) -> str:
        """コード生成プロンプトを構築する。"""
        return f"""Write a complete, production-ready Python 3.10+ module.

File: {task.file}
Purpose: {task.description}

Requirements:
- Full type hints on all functions
- Docstrings on all public functions and classes
- Proper error handling with specific exceptions
- No hardcoded configuration

Return ONLY valid Python code. No markdown fences, no explanation.
"""

    def _extract_code(self, raw: str) -> str:
        """
        LLM応答からコードフェンスを除去してクリーンなコードを抽出する。

        Args:
            raw: LLMの生応答テキスト

        Returns:
            コードフェンスを除去したPythonコード文字列
        """
        lines = raw.strip().splitlines()
        # 先頭のコードフェンスを除去
        if lines and any(lines[0].startswith(m) for m in _CODE_FENCE_MARKERS):
            lines = lines[1:]
        # 末尾のコードフェンスを除去
        if lines and lines[-1].strip() in ("```", "~~~"):
            lines = lines[:-1]
        return "\n".join(lines)