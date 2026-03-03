
# =============================================================================
# agentic_coder/domain/exceptions.py
# =============================================================================
# カスタム例外 — 全失敗モードを型付きで表現する
# =============================================================================

from __future__ import annotations


class AgentError(Exception):
    """エージェント基底例外 — 全ドメイン例外の親クラス。"""


class LLMCallError(AgentError):
    """LLM呼び出し失敗時に送出される例外。"""


class EmbeddingError(AgentError):
    """埋め込みベクトル生成失敗時に送出される例外。"""


class PlanParseError(AgentError):
    """LLMからの計画JSONパース失敗時に送出される例外。"""


class CodeExecutionError(AgentError):
    """生成コードの実行失敗時に送出される例外。"""


class TestExecutionError(AgentError):
    """テスト実行失敗時に送出される例外。"""


class MaxRetriesExceededError(AgentError):
    """最大デバッグ試行回数超過時に送出される例外。"""

    def __init__(self, filename: str, retries: int) -> None:
        super().__init__(f"{filename} のデバッグが {retries} 回試行後も失敗した")
        self.filename = filename
        self.retries = retries


class MemoryError(AgentError):
    """メモリ操作失敗時に送出される例外。"""