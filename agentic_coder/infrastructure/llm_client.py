
# =============================================================================
# agentic_coder/infrastructure/llm_client.py
# =============================================================================
# LLMクライアント — Ollamaとの通信を抽象化するインフラ層
# =============================================================================

from __future__ import annotations

import logging
from typing import Protocol

import requests

from ..config import OllamaConfig
from ..domain.exceptions import LLMCallError

logger = logging.getLogger(__name__)


class LLMClientProtocol(Protocol):
    """LLMクライアントの抽象インターフェース — DIによるテスト差し替えを可能にする。"""

    def generate(self, prompt: str) -> str:
        """プロンプトを送信しテキスト応答を返す。"""
        ...


class OllamaLLMClient:
    """
    Ollamaのgenerate APIを呼び出すLLMクライアント実装。

    Args:
        config: Ollama接続設定
    """

    def __init__(self, config: OllamaConfig) -> None:
        self._config = config
        self._endpoint = f"{config.base_url}/generate"

    def generate(self, prompt: str) -> str:
        """
        LLMにプロンプトを送信しテキスト応答を返す。

        Args:
            prompt: LLMへの入力プロンプト

        Returns:
            LLMが生成したテキスト

        Raises:
            LLMCallError: HTTP通信失敗またはレスポンス形式不正時
        """
        logger.debug("LLM呼び出し開始 | endpoint=%s | prompt_len=%d", self._endpoint, len(prompt))
        try:
            response = requests.post(
                self._endpoint,
                json={"model": self._config.model, "prompt": prompt, "stream": False},
                timeout=self._config.timeout_seconds,
            )
            response.raise_for_status()
            text: str = response.json()["response"]
            logger.debug("LLM応答受信 | response_len=%d", len(text))
            return text
        except requests.RequestException as exc:
            raise LLMCallError(f"Ollama generate API呼び出し失敗: {exc}") from exc
        except (KeyError, ValueError) as exc:
            raise LLMCallError(f"Ollamaレスポンス形式不正: {exc}") from exc