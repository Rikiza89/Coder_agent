
# =============================================================================
# agentic_coder/infrastructure/memory_store.py
# =============================================================================
# メモリストア — SQLiteを使用した安全な永続化レイヤー
# pickleではなくSQLiteを使用 — セキュリティと堅牢性のため
# =============================================================================

from __future__ import annotations

import json
import logging
import math
import sqlite3
from contextlib import contextmanager
from typing import Generator

from ..config import MemoryConfig
from ..domain.exceptions import MemoryError as AgentMemoryError
from ..domain.models import MemoryEntry
from ..infrastructure.embedder import EmbedderProtocol

logger = logging.getLogger(__name__)


class MemoryStore:
    """
    SQLiteバックエンドを使用したベクトルメモリストア。

    pickleの代わりにSQLiteを使用することで:
    - デシリアライズ攻撃リスクを排除
    - クエリ可能な永続化を実現
    - 並行アクセス安全性を向上

    Args:
        config: メモリ設定
        embedder: 埋め込みクライアント実装
    """

    def __init__(self, config: MemoryConfig, embedder: EmbedderProtocol) -> None:
        self._config = config
        self._embedder = embedder
        self._db_path = config.db_path
        self._init_db()

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        """DBコネクションのコンテキストマネージャー — 常にコミットまたはロールバックを保証する。"""
        conn = sqlite3.connect(self._db_path)
        try:
            yield conn
            conn.commit()
        except sqlite3.Error as exc:
            conn.rollback()
            raise AgentMemoryError(f"DB操作失敗: {exc}") from exc
        finally:
            conn.close()

    def _init_db(self) -> None:
        """メモリテーブルを初期化する — 冪等な操作。"""
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        logger.debug("メモリDBを初期化 | path=%s", self._db_path)

    def add(self, text: str) -> None:
        """
        テキストをメモリに追加する。

        Args:
            text: 記憶するテキスト内容

        Raises:
            EmbeddingError: 埋め込み生成失敗時
            AgentMemoryError: DB書き込み失敗時
        """
        embedding = self._embedder.embed(text)
        embedding_json = json.dumps(embedding)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO memories (text, embedding) VALUES (?, ?)",
                (text, embedding_json),
            )
        logger.info("メモリに追加 | text_preview=%s", text[:60])

    def retrieve(self, query: str) -> str:
        """
        クエリに最も類似したメモリを取得する。
        コサイン類似度によるベクトル検索を実行する。

        Args:
            query: 検索クエリテキスト

        Returns:
            上位k件のメモリを改行区切りで結合した文字列

        Raises:
            EmbeddingError: クエリ埋め込み生成失敗時
        """
        query_vec = self._embedder.embed(query)

        with self._connect() as conn:
            rows = conn.execute("SELECT text, embedding FROM memories").fetchall()

        if not rows:
            return ""

        scored: list[tuple[float, str]] = []
        for text, emb_json in rows:
            emb = json.loads(emb_json)
            score = self._cosine_similarity(query_vec, emb)
            scored.append((score, text))

        # スコア降順でソートし上位k件を返す
        scored.sort(reverse=True)
        top_k = self._config.top_k_retrieval
        return "\n".join(text for _, text in scored[:top_k])

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """
        2つのベクトルのコサイン類似度を計算する。
        numpyへの依存を排除し、標準ライブラリのみで実装。

        Args:
            a: ベクトルA
            b: ベクトルB

        Returns:
            コサイン類似度スコア (-1.0 〜 1.0)
        """
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)