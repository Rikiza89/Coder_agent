
# =============================================================================
# agentic_coder/__main__.py
# =============================================================================
# パッケージエントリポイント — `python -m agentic_coder` で起動する
# =============================================================================

from __future__ import annotations

import logging
import sys

from .config import AppConfig
from .main import build_orchestrator
from .ui.app import run


def main() -> None:
    """
    UIモードでアプリケーションを起動する。
    設定を検証してからUIファクトリに渡す。
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )

    # UIはファクトリ経由でオーケストレーターを生成する
    # これにより作業ディレクトリ変更時の再生成が可能になる
    sys.exit(run(build_orchestrator))


if __name__ == "__main__":
    main()