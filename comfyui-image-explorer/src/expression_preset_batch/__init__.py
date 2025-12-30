"""
expression_preset_batch package

ExpressionPresetNode 前提で、expression×seed のバッチ実行を行うツール群。

ここでは外部に公開したい最低限の型だけを再exportする。
（移行中の破綻を避けるため、try/except で保険を掛ける）
"""

from __future__ import annotations

try:
    from .models import (
        Expression,
        ExpressionPresetNodeMapping,
        GenerationParams,
        normalize_expressions,
    )
except Exception:  # pragma: no cover
    Expression = None  # type: ignore
    ExpressionPresetNodeMapping = None  # type: ignore
    GenerationParams = None  # type: ignore
    normalize_expressions = None  # type: ignore


__all__ = [
    "Expression",
    "ExpressionPresetNodeMapping",
    "GenerationParams",
    "normalize_expressions",
]

__version__ = "0.1.0"
