
# =============================================================================
# agentic_coder/infrastructure/embedder.py
# =============================================================================
# 埋め込みクライアント — テキストをベクトルに変換するインフラ層
# =============================================================================

from __future__ import annotations

import logging
from typing import Protocol

import requests

from ..config import OllamaConfig
from ..domain.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class EmbedderProtocol(Protocol):
    """埋め込みクライアントの抽象インターフェース。"""

    def embed(self, text: str) -> list[float]:
        """テキストを埋め込みベクトルに変換する。"""
        ...


class OllamaEmbedder:
    """
    OllamaのEmbeddings APIを使用した埋め込みクライアント。

    Args:
        config: Ollama接続設定
    """

    def __init__(self, config: OllamaConfig) -> None:
        self._config = config
        self._endpoint = f"{config.base_url}/embeddings"

    def embed(self, text: str) -> list[float]:
        """
        テキストを埋め込みベクトルに変換する。

        Args:
            text: 埋め込み対象テキスト

        Returns:
            float値のリストとして表現された埋め込みベクトル

        Raises:
            EmbeddingError: HTTP通信失敗またはレスポンス形式不正時
        """
        try:
            response = requests.post(
                self._endpoint,
                json={"model": self._config.embed_model, "prompt": text},
                timeout=self._config.timeout_seconds,
            )
            response.raise_for_status()
            return list(response.json()["embedding"])
        except requests.RequestException as exc:
            raise EmbeddingError(f"Ollama embeddings API呼び出し失敗: {exc}") from exc
        except (KeyError, ValueError) as exc:
            raise EmbeddingError(f"埋め込みレスポンス形式不正: {exc}") from exc