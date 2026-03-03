
# =============================================================================
# agentic_coder/infrastructure/code_runner.py
# =============================================================================
# コード実行インフラ — サブプロセス操作を安全にカプセル化する
# =============================================================================

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

from ..domain.exceptions import CodeExecutionError, TestExecutionError

logger = logging.getLogger(__name__)

# サブプロセスタイムアウト — リソース枯渇を防ぐ
_SUBPROCESS_TIMEOUT = int(os.getenv("SUBPROCESS_TIMEOUT", "60"))


class CodeRunner:
    """
    Pythonファイルとpytestを安全に実行するインフラクラス。

    攻撃面: サブプロセス経由でLLM生成コードを実行するため、
    信頼できない環境での実行には別途サンドボックスが必要。
    """

    def run_file(self, filepath: Path) -> str:
        """
        Pythonファイルをサブプロセスで実行する。

        Args:
            filepath: 実行対象ファイルパス

        Returns:
            標準出力と標準エラーの結合文字列

        Raises:
            CodeExecutionError: ファイルが存在しない場合
        """
        if not filepath.exists():
            raise CodeExecutionError(f"実行対象ファイルが存在しない: {filepath}")

        logger.info("ファイル実行 | path=%s", filepath)
        result = subprocess.run(
            [sys.executable, str(filepath)],
            capture_output=True,
            text=True,
            timeout=_SUBPROCESS_TIMEOUT,
        )
        return result.stdout + result.stderr

    def run_tests(self, test_dir: Path) -> tuple[bool, str]:
        """
        指定ディレクトリでpytestを実行する。

        Args:
            test_dir: テスト実行ディレクトリ

        Returns:
            (成功フラグ, テスト出力文字列) のタプル

        Raises:
            TestExecutionError: pytest実行自体が失敗した場合
        """
        logger.info("テスト実行 | dir=%s", test_dir)
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", str(test_dir)],
                capture_output=True,
                text=True,
                timeout=_SUBPROCESS_TIMEOUT,
            )
        except subprocess.TimeoutExpired as exc:
            raise TestExecutionError("pytest実行がタイムアウトした") from exc
        except FileNotFoundError as exc:
            raise TestExecutionError("pytestが見つからない — インストールを確認せよ") from exc

        output = result.stdout + result.stderr
        # テスト失敗判定 — returncode非ゼロまたは"failed"文字列の存在
        passed = result.returncode == 0 and "failed" not in output.lower()
        return passed, output