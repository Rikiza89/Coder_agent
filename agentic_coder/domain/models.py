
# =============================================================================
# agentic_coder/domain/models.py
# =============================================================================
# ドメインモデル — ビジネスエンティティをフレームワーク非依存で定義する
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class TaskStatus(Enum):
    """タスク処理状態の列挙型。"""
    PENDING = auto()
    CODING = auto()
    TESTING = auto()
    DEBUGGING = auto()
    COMPLETE = auto()
    FAILED = auto()


@dataclass
class FileTask:
    """
    単一ファイル生成タスクのドメインモデル。

    Args:
        file: 生成対象ファイル名
        description: ファイルの役割説明
        status: 現在の処理状態
        attempt_count: デバッグ試行回数
        error_log: 直近のエラー出力
    """
    file: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    attempt_count: int = 0
    error_log: Optional[str] = None


@dataclass
class ProjectPlan:
    """
    プロジェクト計画全体を表すドメインモデル。

    Args:
        goal: ユーザーの自然言語目標
        tasks: 実行すべきファイルタスクのリスト
    """
    goal: str
    tasks: list[FileTask] = field(default_factory=list)


@dataclass(frozen=True)
class MemoryEntry:
    """
    メモリストアの単一エントリ。

    Args:
        text: 記憶するテキスト内容
        embedding: テキストの埋め込みベクトル (float のリスト)
    """
    text: str
    embedding: list[float]