"""
image_explorer package

- 画像生成の組み合わせ探索（prompt axis exploration）向けモジュール群。
- 外部に公開する“入口”として、主要クラス/関数だけをここで再エクスポートする。

方針:
- 依存関係の循環を避けるため、ここでは“軽い import”に留める。
- 後で整理する場合は __all__ を見れば公開APIが分かる状態にする。
"""

from __future__ import annotations

# Public API re-exports
# NOTE: ファイル移動/リファクタの過渡期では import エラーになりやすいので、
#       まずは実在するモジュールに合わせて調整してください。

try:
    from .prompt_builder import PromptBuilder, ParameterCombinationGenerator
except Exception:  # pragma: no cover
    # まだ分割途中でもパッケージ import 自体は通したい場合の保険
    PromptBuilder = None  # type: ignore
    ParameterCombinationGenerator = None  # type: ignore


__all__ = [
    "PromptBuilder",
    "ParameterCombinationGenerator",
]

# 任意: バージョンを付けたい場合（git tag運用にするなら削ってOK）
__version__ = "0.1.0"
