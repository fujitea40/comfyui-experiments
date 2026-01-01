"""
プロンプト構築とランダム選択のロジック
探索軸と非探索軸の選択方法を制御する
"""

import itertools
import logging
from typing import Dict, Iterator, List, Tuple

from comfytools.core_models import (
    GenerationParams,
    LoraConfig,
    PromptTemplate,
    SamplerConfig,
    WeightedPrompt,
)
from comfytools.utils import join_prompts, pick_from_choices

logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    プロンプトを構築するクラス
    探索軸の全候補と非探索軸のランダム選択を管理
    """

    def __init__(
        self, prompt_template: PromptTemplate, randomize_non_target: bool = True
    ):
        """
        Args:
            prompt_template: プロンプトテンプレート
            randomize_non_target: 非探索軸をランダム化するか
        """
        self.template = prompt_template
        self.randomize_non_target = randomize_non_target
        logger.info(f"PromptBuilderを初期化しました（軸: {len(self.template.axes)}）")

    def get_axis_choices(self, axis_name: str, is_target: bool) -> List[str]:
        """
        指定された軸の選択肢を取得

        Args:
            axis_name: 軸の名前
            is_target: 探索対象の軸かどうか

        Returns:
            List[str]: 選択肢のリスト
                - 探索軸: すべての候補
                - 非探索軸（ランダム化ON）: ランダムに選んだ1個
                - 非探索軸（ランダム化OFF）: 最初の1個
        """
        axis = self.template.get_axis_by_name(axis_name)

        if is_target:
            # 探索軸: すべての候補を返す（文字列に変換）
            return axis.get_all_values()
        else:
            # 非探索軸
            if self.randomize_non_target:
                # ランダムに1個選択（文字列として返す）
                choice = pick_from_choices(axis.choices)
                # WeightedPromptオブジェクトの場合は.textを取得
                if isinstance(choice, WeightedPrompt):
                    return [choice.text]
                return [choice]
            else:
                # 最初の1個を返す
                return [axis.get_all_values()[0]]

    def create_axis_combinations(self, target_axis_name: str) -> List[Dict[str, str]]:
        """
        すべての軸の組み合わせを生成

        Args:
            target_axis_name: 探索対象の軸名

        Returns:
            List[Dict[str, str]]: 各組み合わせの辞書のリスト
                例: [{"hair_style": "long hair", "expression": "smile", ...}, ...]
        """
        # 各軸の選択肢を取得
        axis_choices_map = {}
        for axis in self.template.axes:
            is_target = axis.name == target_axis_name
            choices = self.get_axis_choices(axis.name, is_target)
            axis_choices_map[axis.name] = choices

        # 組み合わせを生成
        axis_names = [axis.name for axis in self.template.axes]
        choices_lists = [axis_choices_map[name] for name in axis_names]

        combinations = []
        for combo in itertools.product(*choices_lists):
            combo_dict = dict(zip(axis_names, combo))
            combinations.append(combo_dict)

        logger.info(f"軸の組み合わせを生成しました: {len(combinations)} パターン")
        return combinations

    def build_positive_prompt(self, axis_values: Dict[str, str]) -> str:
        """
        ポジティブプロンプトを構築

        Args:
            axis_values: 各軸の値 {"hair_style": "long hair", ...}

        Returns:
            str: 構築されたプロンプト
        """
        # 固定部分 + 可変部分
        parts = self.template.fixed_positive + list(axis_values.values())
        return join_prompts(parts)

    def build_negative_prompt(self) -> str:
        """
        ネガティブプロンプトを構築

        Returns:
            str: ネガティブプロンプト
        """
        return join_prompts(self.template.negative)

    def build_prompts(self, axis_values: Dict[str, str]) -> Tuple[str, str]:
        """
        ポジティブとネガティブのプロンプトを構築

        Args:
            axis_values: 各軸の値

        Returns:
            Tuple[str, str]: (positive_prompt, negative_prompt)
        """
        positive = self.build_positive_prompt(axis_values)
        negative = self.build_negative_prompt()
        return positive, negative


class ParameterCombinationGenerator:
    """
    パラメータの組み合わせを生成するクラス
    プロンプト + サンプラー + LoRAの全組み合わせ
    """

    def __init__(
        self,
        prompt_builder: PromptBuilder,
        sampler_choices: Dict[str, List],
        lora_choices: Dict[str, Dict[str, List]],
    ):
        """
        Args:
            prompt_builder: プロンプトビルダー
            sampler_choices: サンプラーの選択肢
            lora_choices: LoRAの選択肢
        """
        self.prompt_builder = prompt_builder
        self.sampler_choices = sampler_choices
        self.lora_choices = lora_choices

    def generate_combinations(
        self, target_axis_name: str
    ) -> Iterator[GenerationParams]:
        """
        すべてのパラメータ組み合わせを生成

        Args:
            target_axis_name: 探索対象の軸名

        Yields:
            GenerationParams: 生成パラメータ
        """
        # 軸の組み合わせを生成
        axis_combinations = self.prompt_builder.create_axis_combinations(
            target_axis_name
        )

        # サンプラーの組み合わせ
        sampler_combos = list(
            itertools.product(
                self.sampler_choices["steps"],
                self.sampler_choices["cfg"],
                self.sampler_choices["sampler_name"],
                self.sampler_choices["scheduler"],
            )
        )

        # LoRAの組み合わせ

        lora_combos = list(
            itertools.product(
                self.lora_choices["names"],
                self.lora_choices["model_strength"],
                self.lora_choices["clip_strength"],
            )
        )

        # すべての組み合わせを生成
        total = len(axis_combinations) * len(sampler_combos) * len(lora_combos)
        logger.info(f"生成パラメータの組み合わせ: {total} 個")

        for axis_values in axis_combinations:
            # プロンプトを構築
            positive, negative = self.prompt_builder.build_prompts(axis_values)

            for steps, cfg, sampler_name, scheduler in sampler_combos:
                for lora_name, lora_model, lora_clip in lora_combos:
                    yield GenerationParams(
                        positive_prompt=positive,
                        negative_prompt=negative,
                        sampler=SamplerConfig(
                            steps=steps,
                            cfg=cfg,
                            sampler_name=sampler_name,
                            scheduler=scheduler,
                            seed=0,  # seedは後で設定
                        ),
                        lora=LoraConfig(
                            name=lora_name,
                            model_strength=lora_model,
                            clip_strength=lora_clip,
                        ),
                        target_axis_name=target_axis_name,
                        prompt_values=axis_values,
                    )

    def count_combinations(self, target_axis_name: str) -> int:
        """
        組み合わせの総数を計算

        Args:
            target_axis_name: 探索対象の軸名

        Returns:
            int: 組み合わせの総数
        """
        axis_combinations = self.prompt_builder.create_axis_combinations(
            target_axis_name
        )

        sampler_count = (
            len(self.sampler_choices["steps"])
            * len(self.sampler_choices["cfg"])
            * len(self.sampler_choices["sampler_name"])
            * len(self.sampler_choices["scheduler"])
        )

        lora_count = (
            len(self.lora_choices["names"])
            * len(self.lora_choices["model_strength"])
            * len(self.lora_choices["clip_strength"])
        )

        return len(axis_combinations) * sampler_count * lora_count


# ====== 便利な関数 ======


def create_prompt_builder(
    prompt_template: PromptTemplate, randomize_non_target: bool = True
) -> PromptBuilder:
    """
    PromptBuilderのファクトリ関数

    Args:
        prompt_template: プロンプトテンプレート
        randomize_non_target: 非探索軸をランダム化するか

    Returns:
        PromptBuilder
    """
    return PromptBuilder(prompt_template, randomize_non_target)


def create_parameter_generator(
    prompt_builder: PromptBuilder,
    sampler_choices: Dict[str, List],
    lora_choices: Dict[str, Dict[str, List]],
) -> ParameterCombinationGenerator:
    """
    ParameterCombinationGeneratorのファクトリ関数

    Args:
        prompt_builder: プロンプトビルダー
        sampler_choices: サンプラーの選択肢
        lora_choices: LoRAの選択肢

    Returns:
        ParameterCombinationGenerator
    """
    return ParameterCombinationGenerator(prompt_builder, sampler_choices, lora_choices)


# ====== 使用例 ======


def example_usage():
    """使用例"""
    from pathlib import Path

    from image_explorer.config.config_loader import ConfigLoader

    # 設定を読み込み
    loader = ConfigLoader(Path("config.yaml"))
    prompt_template = loader.load_prompt_template()
    sampler_choices = loader.load_sampler_choices()
    lora_choices = loader.load_lora_choices()

    # PromptBuilderを作成
    builder = PromptBuilder(prompt_template, randomize_non_target=True)

    # 探索軸を指定
    target_axis_name = "hair_style"

    # 軸の組み合わせを生成
    combinations = builder.create_axis_combinations(target_axis_name)
    print(f"軸の組み合わせ: {len(combinations)} パターン")

    # 最初の組み合わせを表示
    first_combo = combinations[0]
    print("\n最初の組み合わせ:")
    for axis_name, value in first_combo.items():
        print(f"  {axis_name}: {value}")

    # プロンプトを構築
    positive, negative = builder.build_prompts(first_combo)
    print(f"\nポジティブプロンプト:\n{positive}")
    print(f"\nネガティブプロンプト:\n{negative}")

    # ParameterCombinationGeneratorを作成
    generator = ParameterCombinationGenerator(builder, sampler_choices, lora_choices)

    # 組み合わせの総数を計算
    total_count = generator.count_combinations(target_axis_name)
    print(f"\n生成される画像の総数: {total_count}")

    # 最初の3個のパラメータを生成
    print("\n最初の3個のパラメータ:")
    for i, params in enumerate(generator.generate_combinations(target_axis_name)):
        if i >= 3:
            break
        print(f"\n--- パラメータ {i + 1} ---")
        print(f"プロンプト: {params.positive_prompt[:50]}...")
        print(f"Steps: {params.sampler.steps}")
        print(f"CFG: {params.sampler.cfg}")
        print(f"Sampler: {params.sampler.sampler_name}")
        print(f"LoRA: {params.lora.name}")


def example_comparison():
    """ランダム化ON/OFFの比較例"""
    from pathlib import Path

    from image_explorer.config.config_loader import ConfigLoader

    loader = ConfigLoader(Path("config.yaml"))
    prompt_template = loader.load_prompt_template()

    target_axis_name = "hair_style"

    # ランダム化ON
    builder_random = PromptBuilder(prompt_template, randomize_non_target=True)
    combos_random = builder_random.create_axis_combinations(target_axis_name)

    # ランダム化OFF
    builder_fixed = PromptBuilder(prompt_template, randomize_non_target=False)
    combos_fixed = builder_fixed.create_axis_combinations(target_axis_name)

    print("=== ランダム化ON ===")
    print(f"組み合わせ数: {len(combos_random)}")
    print(f"最初の組み合わせ: {combos_random[0]}")

    print("\n=== ランダム化OFF ===")
    print(f"組み合わせ数: {len(combos_fixed)}")
    print(f"最初の組み合わせ: {combos_fixed[0]}")

    print(f"\n組み合わせ数の差: {len(combos_random) - len(combos_fixed)}")


def example_full_generation():
    """完全な生成例（メインループのシミュレーション）"""
    from pathlib import Path

    from comfytools.utils import generate_seed
    from image_explorer.config.config_loader import ConfigLoader

    loader = ConfigLoader(Path("config.yaml"))
    prompt_template = loader.load_prompt_template()
    sampler_choices = loader.load_sampler_choices()
    lora_choices = loader.load_lora_choices()
    execution_config = loader.load_execution_config()

    # PromptBuilderを作成
    builder = PromptBuilder(
        prompt_template, randomize_non_target=execution_config.randomize_non_target
    )

    # ParameterCombinationGeneratorを作成
    generator = ParameterCombinationGenerator(builder, sampler_choices, lora_choices)

    # 探索軸を指定
    target_axis_name = "expression"

    # 組み合わせの総数を計算
    total = generator.count_combinations(target_axis_name)
    total_with_repeats = total * execution_config.repeats

    print(f"探索軸: {target_axis_name}")
    print(f"1回あたりの生成数: {total}")
    print(f"繰り返し: {execution_config.repeats}")
    print(f"合計生成数: {total_with_repeats}")

    # パラメータを生成して表示（最初の2個だけ）
    print("\n--- 生成パラメータのサンプル ---")
    for i, params in enumerate(generator.generate_combinations(target_axis_name)):
        if i >= 2:
            break

        # seedを設定
        params.sampler.seed = generate_seed()

        print(f"\nパラメータ {i + 1}:")
        print(f"  軸の値: {params.prompt_values}")
        print(f"  ポジティブ: {params.positive_prompt[:60]}...")
        print(
            f"  サンプラー: {params.sampler.sampler_name} +(steps={params.sampler.steps}, cfg={params.sampler.cfg})"  # noqa: E501
        )
        print(f"  Seed: {params.sampler.seed}")


if __name__ == "__main__":
    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    example_usage()
    # example_comparison()
    # example_full_generation()
