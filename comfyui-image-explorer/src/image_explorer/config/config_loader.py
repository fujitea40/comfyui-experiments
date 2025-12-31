"""
設定ファイル（YAML/JSON）からデータクラスを生成するローダー
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Union

import yaml

from comfytools.core_models import (
    ExecutionConfig,
    NodeMapping,
    PromptAxis,
    PromptTemplate,
    WeightedPrompt,
    WorkflowConfig,
)

logger = logging.getLogger(__name__)


# ====== 個別のローダー関数 ======


def load_weighted_prompt(
    data: Union[str, Dict[str, Any]],
) -> Union[str, WeightedPrompt]:
    """
    文字列または辞書からプロンプトを生成

    Args:
        data: 文字列 or {"text": "...", "weight": ...}

    Returns:
        str or WeightedPrompt

    Examples:
        >>> load_weighted_prompt("smile")
        'smile'

        >>> load_weighted_prompt({"text": "smile", "weight": 1.5})
        WeightedPrompt(text='smile', weight=1.5)
    """
    if isinstance(data, str):
        return data
    elif isinstance(data, dict):
        return WeightedPrompt(text=data["text"], weight=data.get("weight", 1.0))
    else:
        raise ValueError(f"不正なプロンプト形式: {type(data)}")


def load_prompt_axis(data: Dict[str, Any]) -> PromptAxis:
    """
    辞書からPromptAxisを生成

    Args:
        data: {"name": "...", "choices": [...]}

    Returns:
        PromptAxis

    Examples:
        >>> data = {
        ...     "name": "hair_style",
        ...     "choices": ["long hair", "short hair"]
        ... }
        >>> axis = load_prompt_axis(data)
        >>> axis.name
        'hair_style'
    """
    if "name" not in data:
        raise ValueError("PromptAxisには'name'フィールドが必要です")
    if "choices" not in data:
        raise ValueError("PromptAxisには'choices'フィールドが必要です")

    return PromptAxis(
        name=data["name"], choices=[load_weighted_prompt(c) for c in data["choices"]]
    )


def load_prompt_template(data: Dict[str, Any]) -> PromptTemplate:
    """
    辞書からPromptTemplateを生成

    Args:
        data: {"fixed_positive": [...], "axes": [...], "negative": [...]}

    Returns:
        PromptTemplate
    """
    if "fixed_positive" not in data:
        raise ValueError("PromptTemplateには'fixed_positive'フィールドが必要です")
    if "axes" not in data:
        raise ValueError("PromptTemplateには'axes'フィールドが必要です")
    if "negative" not in data:
        raise ValueError("PromptTemplateには'negative'フィールドが必要です")

    return PromptTemplate(
        fixed_positive=data["fixed_positive"],
        axes=[load_prompt_axis(axis) for axis in data["axes"]],
        negative=data["negative"],
    )


def load_node_mapping(data: Dict[str, Any]) -> NodeMapping:
    """
    辞書からNodeMappingを生成

    Args:
        data: ノードIDのマッピング辞書

    Returns:
        NodeMapping
    """
    required_fields = [
        "positive_prompt",
        "negative_prompt",
        "ksampler",
        "empty_latent",
        "save_image",
        "lora",
    ]

    for field in required_fields:
        if field not in data:
            raise ValueError(f"NodeMappingには'{field}'フィールドが必要です")

    return NodeMapping(
        positive_prompt=data["positive_prompt"],
        negative_prompt=data["negative_prompt"],
        ksampler=data["ksampler"],
        empty_latent=data["empty_latent"],
        save_image=data["save_image"],
        lora=data["lora"],
    )


def load_workflow_config(data: Dict[str, Any]) -> WorkflowConfig:
    """
    辞書からWorkflowConfigを生成

    Args:
        data: {"json_path": "...", "node_mapping": {...}, "output_root": "..."}

    Returns:
        WorkflowConfig
    """
    if "json_path" not in data:
        raise ValueError("WorkflowConfigには'json_path'フィールドが必要です")
    if "node_mapping" not in data:
        raise ValueError("WorkflowConfigには'node_mapping'フィールドが必要です")
    if "output_root" not in data:
        raise ValueError("WorkflowConfigには'output_root'フィールドが必要です")

    return WorkflowConfig(
        json_path=Path(data["json_path"]),
        node_mapping=load_node_mapping(data["node_mapping"]),
        output_root=Path(data["output_root"]),
    )


def load_execution_config(data: Dict[str, Any]) -> ExecutionConfig:
    """
    辞書からExecutionConfigを生成

    Args:
        data: 実行設定の辞書

    Returns:
        ExecutionConfig
    """
    return ExecutionConfig(
        repeats=data.get("repeats", 2),
        randomize_non_target=data.get("randomize_non_target", True),
        comfy_url=data.get("comfy_url", "http://127.0.0.1:8188"),
        state_file=Path(data.get("state_file", "axis_state.json")),
        poll_interval=data.get("poll_interval", 1.0),
    )


# ====== ファイル読み込み ======


def load_yaml_file(yaml_path: Path) -> Dict[str, Any]:
    """
    YAMLファイルから辞書を読み込み

    Args:
        yaml_path: YAMLファイルのパス

    Returns:
        Dict[str, Any]: 読み込まれた辞書

    Raises:
        FileNotFoundError: ファイルが存在しない
        yaml.YAMLError: YAML構文エラー
    """
    if not yaml_path.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {yaml_path}")

    logger.info(f"YAMLファイルを読み込み中: {yaml_path}")

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        logger.info("YAMLファイルの読み込みに成功しました")
        return data
    except yaml.YAMLError as e:
        logger.error(f"YAML構文エラー: {e}")
        raise


def load_json_file(json_path: Path) -> Dict[str, Any]:
    """
    JSONファイルから辞書を読み込み

    Args:
        json_path: JSONファイルのパス

    Returns:
        Dict[str, Any]: 読み込まれた辞書

    Raises:
        FileNotFoundError: ファイルが存在しない
        json.JSONDecodeError: JSON構文エラー
    """
    if not json_path.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {json_path}")

    logger.info(f"JSONファイルを読み込み中: {json_path}")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("JSONファイルの読み込みに成功しました")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON構文エラー: {e}")
        raise


# ====== メインローダークラス ======


class ConfigLoader:
    """
    設定ファイルから全設定をロードするクラス
    YAML/JSON両対応
    """

    def __init__(self, config_path: Path):
        """
        Args:
            config_path: 設定ファイルのパス（.yaml, .yml, .json）

        Raises:
            ValueError: 未対応のファイル形式
            FileNotFoundError: ファイルが存在しない
        """
        self.config_path = config_path

        # ファイル形式に応じて読み込み
        suffix = config_path.suffix.lower()
        if suffix in [".yaml", ".yml"]:
            self.raw_data = load_yaml_file(config_path)
        elif suffix == ".json":
            self.raw_data = load_json_file(config_path)
        else:
            raise ValueError(
                f"未対応のファイル形式: {suffix}（.yaml, .yml, .json のみ対応）"
            )

        logger.info(f"設定ファイルを読み込みました: {config_path}")

    # ====== 各種設定の読み込み ======

    def load_prompt_template(self) -> PromptTemplate:
        """
        プロンプトテンプレートを読み込み

        Returns:
            PromptTemplate

        Raises:
            KeyError: 'prompt_template'キーが存在しない
        """
        if "prompt_template" not in self.raw_data:
            raise KeyError("設定ファイルに'prompt_template'セクションが存在しません")

        logger.info("プロンプトテンプレートを読み込み中")
        template = load_prompt_template(self.raw_data["prompt_template"])
        logger.info(
            f"プロンプトテンプレートを読み込みました（{len(template.axes)} 個の軸）"
        )
        return template

    def load_workflow_config(self) -> WorkflowConfig:
        """
        ワークフロー設定を読み込み

        Returns:
            WorkflowConfig

        Raises:
            KeyError: 'workflow'キーが存在しない
        """
        if "workflow" not in self.raw_data:
            raise KeyError("設定ファイルに'workflow'セクションが存在しません")

        logger.info("ワークフロー設定を読み込み中")
        config = load_workflow_config(self.raw_data["workflow"])
        logger.info(f"ワークフロー設定を読み込みました: {config.json_path}")
        return config

    def load_execution_config(self) -> ExecutionConfig:
        """
        実行設定を読み込み

        Returns:
            ExecutionConfig

        Raises:
            KeyError: 'execution'キーが存在しない
        """
        if "execution" not in self.raw_data:
            raise KeyError("設定ファイルに'execution'セクションが存在しません")

        logger.info("実行設定を読み込み中")
        config = load_execution_config(self.raw_data["execution"])
        logger.info(f"実行設定を読み込みました（繰り返し: {config.repeats}）")
        return config

    def load_sampler_choices(self) -> Dict[str, List]:
        """
        サンプラーの選択肢リストを読み込み

        Returns:
            Dict[str, List]: {"steps": [...], "cfg": [...], ...}

        Raises:
            KeyError: 'sampler_choices'キーが存在しない
        """
        if "sampler_choices" not in self.raw_data:
            raise KeyError("設定ファイルに'sampler_choices'セクションが存在しません")

        logger.info("サンプラー選択肢を読み込み中")
        choices = self.raw_data["sampler_choices"]

        # 必須フィールドをチェック
        required = ["steps", "cfg", "sampler_name", "scheduler"]
        for field in required:
            if field not in choices:
                raise ValueError(f"sampler_choicesには'{field}'フィールドが必要です")

        logger.info("サンプラー選択肢を読み込みました")
        return choices

    def load_lora_choices(self) -> Dict[str, Dict[str, List]]:
        """
        LoRAの選択肢リストを読み込み

        Returns:
            Dict: {"standard": {...}, "perky_breasts": {...}}

        Raises:
            KeyError: 'lora_choices'キーが存在しない
        """
        if "lora_choices" not in self.raw_data:
            raise KeyError("設定ファイルに'lora_choices'セクションが存在しません")

        logger.info("LoRA選択肢を読み込み中")
        choices = self.raw_data["lora_choices"]

        logger.info("LoRA選択肢を読み込みました")
        return choices

    # ====== 一括読み込み ======

    def load_all(self) -> Dict[str, Any]:
        """
        すべての設定を一度に読み込み

        Returns:
            Dict: {
                "prompt_template": PromptTemplate,
                "workflow": WorkflowConfig,
                "execution": ExecutionConfig,
                "sampler_choices": Dict,
                "lora_choices": Dict
            }
        """
        logger.info("すべての設定を読み込み中")

        result = {
            "prompt_template": self.load_prompt_template(),
            "workflow": self.load_workflow_config(),
            "execution": self.load_execution_config(),
            "sampler_choices": self.load_sampler_choices(),
            "lora_choices": self.load_lora_choices(),
        }

        logger.info("すべての設定を読み込みました")
        return result


# ====== 便利な関数 ======


def load_config(config_path: Path) -> ConfigLoader:
    """
    ConfigLoaderのファクトリ関数

    Args:
        config_path: 設定ファイルのパス

    Returns:
        ConfigLoader
    """
    return ConfigLoader(config_path)


def quick_load(config_path: Path) -> Dict[str, Any]:
    """
    設定ファイルを読み込んですべての設定を返す（簡易版）

    Args:
        config_path: 設定ファイルのパス

    Returns:
        Dict: すべての設定
    """
    loader = ConfigLoader(config_path)
    return loader.load_all()


# ====== 使用例 ======


def example_usage():
    """使用例"""

    config_path = Path("config.yaml")

    # 方法1: ConfigLoaderを使用
    print("=== 方法1: ConfigLoaderを使用 ===")
    loader = ConfigLoader(config_path)

    # 個別に読み込み
    prompt_template = loader.load_prompt_template()
    workflow_config = loader.load_workflow_config()
    execution_config = loader.load_execution_config()

    print(f"軸の数: {len(prompt_template.axes)}")
    print(f"繰り返し回数: {execution_config.repeats}")
    print(f"出力先: {workflow_config.output_root}")

    # 軸の情報を表示
    for axis in prompt_template.axes:
        print(f"  - {axis.name}: {len(axis.choices)} 個の選択肢")

    # 方法2: 一括読み込み
    print("\n=== 方法2: 一括読み込み ===")
    all_config = loader.load_all()

    print("読み込まれた設定:")
    for key in all_config.keys():
        print(f"  - {key}")

    # 方法3: 簡易版
    print("\n=== 方法3: 簡易版 ===")
    config = quick_load(config_path)
    print(f"実行URL: {config['execution'].comfy_url}")


def example_error_handling():
    """エラーハンドリングの例"""

    config_path = Path("config.yaml")

    try:
        loader = ConfigLoader(config_path)
        config = loader.load_all()  # noqa: F841
        print("設定ファイルの読み込みに成功しました")

    except FileNotFoundError as e:
        print(f"エラー: 設定ファイルが見つかりません - {e}")

    except KeyError as e:
        print(f"エラー: 必須のセクションが存在しません - {e}")

    except ValueError as e:
        print(f"エラー: 設定の形式が不正です - {e}")

    except yaml.YAMLError as e:
        print(f"エラー: YAML構文エラー - {e}")

    except Exception as e:
        print(f"予期しないエラー: {e}")


if __name__ == "__main__":
    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    example_usage()
    # example_error_handling()
