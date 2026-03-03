
# =============================================================================
# agentic_coder/config.py
# =============================================================================
# 設定管理モジュール — 全設定を外部化・型安全に管理する
# =============================================================================

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class OllamaConfig:
    """Ollamaサービスの接続設定。"""
    base_url: str = field(default_factory=lambda: os.getenv("OLLAMA_URL", "http://localhost:11434/api"))
    model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b-instruct-q4_K_M"))
    embed_model: str = field(default_factory=lambda: os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"))
    timeout_seconds: int = field(default_factory=lambda: int(os.getenv("OLLAMA_TIMEOUT", "120")))


@dataclass(frozen=True)
class MemoryConfig:
    """メモリ永続化設定。"""
    db_path: str = field(default_factory=lambda: os.getenv("MEMORY_DB_PATH", "agent_memory.db"))
    top_k_retrieval: int = 3


@dataclass(frozen=True)
class AgentConfig:
    """エージェント動作設定。"""
    max_debug_retries: int = field(default_factory=lambda: int(os.getenv("MAX_DEBUG_RETRIES", "5")))
    output_dir: str = field(default_factory=lambda: os.getenv("OUTPUT_DIR", "output"))


@dataclass(frozen=True)
class AppConfig:
    """アプリケーション全体設定 — 単一の信頼できる設定ソース。"""
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)

    def validate(self) -> None:
        """起動時設定検証 — 不正設定を早期に検出する。"""
        if self.agent.max_debug_retries < 1:
            raise ValueError("MAX_DEBUG_RETRIES は1以上でなければならない")
        if not self.ollama.base_url.startswith("http"):
            raise ValueError("OLLAMA_URL は有効なHTTP URLでなければならない")