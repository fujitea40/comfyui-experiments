"""
models.py

expression_preset_batch (epb) 用のデータモデル定義。

方針:
- image_explorer の models.py と責務が違うものは epb 側に閉じる
- ExpressionPresetNode がプロンプト/paramsを決める前提なので、
  epb 側は「どの expression を実行するか」「seed/出力prefix」などの実行メタに寄せる
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeAlias

# まずは設定ファイルに書く値をそのまま通す（必要になったら Enum/Literal に強化）
Expression: TypeAlias = str


@dataclass(frozen=True)
class ExpressionPresetNodeMapping:
    """
    ExpressionPresetNode の差し替え先を表すマッピング。

    想定:
    - workflow内に ExpressionPresetNode があり、その inputs の一つに expression 名を渡す
    - 例: node.inputs["expression"] = "smile"
    """

    node_id: str
    expression_input_name: str = "expression"

    # 将来拡張（必要になったら使う）
    # - common_prompt_input_name: Optional[str] = None
    # 例: 共通プロンプト追記欄がある場合
    # - params_output_linked: bool = True
    # 例: 下流がリンクで接続されている前提など

    def validate(self) -> None:
        if not self.node_id:
            raise ValueError("ExpressionPresetNodeMapping.node_id must be non-empty.")
        if not self.expression_input_name:
            raise ValueError(
                "ExpressionPresetNodeMapping.expression_input_name must be non-empty."
            )


@dataclass
class GenerationParams:
    """
    epbで「1回の実行」を表すパラメータ。

    image_explorer の GenerationParams と違い、ここでは
    - expression 名
    - seed
    - 出力ディレクトリ/ファイルprefix
    - 追加メタ（将来拡張）
    を主に持つ。

    注:
    - repeats は ExecutionConfig 側に持たせても良いが、
      「この実行アイテムは何回繰り返すか」を持たせたい場合もあるので optional にしている。
    """  # noqa: E501

    expression: Expression
    seed: int

    # SaveImage の filename_prefix に設定する値（例: "{run_id}/img"）
    filename_prefix: str = "img"

    # 出力先（ツール側で管理する場合に使用。ComfyUI側が絶対パス保存しない構成でもメタ用途に） # noqa: E501
    output_dir: Optional[Path] = None

    # 必要なら個別に上書きできるように（Noneなら ExecutionConfig の repeats を採用、など） # noqa: E501
    repeats: Optional[int] = None

    # 将来拡張用（expression以外の追加指示を入れたい場合に使う）
    extras: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.expression, str) or not self.expression.strip():
            raise ValueError("GenerationParams.expression must be a non-empty string.")
        if not isinstance(self.seed, int):
            raise ValueError("GenerationParams.seed must be int.")
        # ComfyUIでは seed=-1 を「ランダム」扱いにする流儀もあるので許容する
        # ただし極端な値は弾いておく
        if self.seed < -1:
            raise ValueError("GenerationParams.seed must be >= -1.")
        if self.repeats is not None and self.repeats <= 0:
            raise ValueError(
                "GenerationParams.repeats must be positive when specified."
            )
        if (
            not isinstance(self.filename_prefix, str)
            or not self.filename_prefix.strip()
        ):
            raise ValueError(
                "GenerationParams.filename_prefix must be a non-empty string."
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expression": self.expression,
            "seed": self.seed,
            "filename_prefix": self.filename_prefix,
            "output_dir": str(self.output_dir) if self.output_dir is not None else None,
            "repeats": self.repeats,
            "extras": self.extras,
        }


# 便利: YAML側の expressions を軽く正規化したい場合に使える
def normalize_expressions(expressions: List[str]) -> List[Expression]:
    """
    - 前後空白を除去
    - 空要素を除外
    - 重複を保持したくない場合はここで set 化も可能（現状は順序維持のまま）
    """
    normalized: List[Expression] = []
    for e in expressions:
        if not isinstance(e, str):
            continue
        s = e.strip()
        if not s:
            continue
        normalized.append(s)
    return normalized
