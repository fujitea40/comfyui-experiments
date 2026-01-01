"""
ComfyUIワークフローJSONの読み込みと操作
"""

import copy
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from comfytools.core_models import (
    GenerationParams,
    LoraConfig,
    SamplerConfig,
    WorkflowConfig,
)

logger = logging.getLogger(__name__)


class WorkflowManager:
    """
    ComfyUIワークフローを管理するクラス
    ワークフローJSONの読み込み、パラメータの設定、コピーを行う
    """

    def __init__(self, workflow_config: WorkflowConfig):
        """
        Args:
            workflow_config: ワークフロー設定

        Raises:
            FileNotFoundError: ワークフローJSONが見つからない
        """
        self.config = workflow_config
        self.base_workflow = self._load_workflow()
        logger.info(f"ワークフローを読み込みました: {workflow_config.json_path}")

    def _load_workflow(self) -> Dict[str, Any]:
        """
        ワークフローJSONを読み込む

        Returns:
            Dict[str, Any]: ワークフローの辞書

        Raises:
            FileNotFoundError: ファイルが存在しない
            json.JSONDecodeError: JSON構文エラー
        """
        json_path = self.config.json_path

        if not json_path.exists():
            raise FileNotFoundError(
                f"ワークフローファイルが見つかりません: {json_path}"
            )

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                workflow = json.load(f)
            logger.info(f"ワークフローJSONを読み込みました（{len(workflow)} ノード）")
            return workflow
        except json.JSONDecodeError as e:
            logger.error(f"ワークフローJSON構文エラー: {e}")
            raise

    def get_base_workflow(self) -> Dict[str, Any]:
        """
        ベースワークフローのコピーを取得
        元のワークフローは変更されない

        Returns:
            Dict[str, Any]: ワークフローのディープコピー
        """
        return copy.deepcopy(self.base_workflow)

    def create_configured_workflow(self, params: GenerationParams) -> Dict[str, Any]:
        """
        GenerationParamsを使ってワークフローを設定

        Args:
            params: 生成パラメータ

        Returns:
            Dict[str, Any]: 設定済みワークフロー
        """
        workflow = self.get_base_workflow()
        self.apply_params(workflow, params)
        return workflow

    def apply_params(self, workflow: Dict[str, Any], params: GenerationParams):
        """
        ワークフローにパラメータを適用（インプレース）

        Args:
            workflow: ワークフロー辞書
            params: 生成パラメータ
        """
        node_mapping = self.config.node_mapping

        # プロンプトを設定
        self._set_prompt(workflow, node_mapping.positive_prompt, params.positive_prompt)
        self._set_prompt(workflow, node_mapping.negative_prompt, params.negative_prompt)

        # サンプラーを設定
        self._set_sampler(workflow, node_mapping.ksampler, params.sampler)

        # LoRAを設定
        self._set_lora(workflow, node_mapping.lora, params.lora)

        logger.debug("ワークフローにパラメータを適用しました")

    # ====== 個別ノード設定 ======

    def _set_prompt(self, workflow: Dict[str, Any], node_id: str, prompt_text: str):
        """
        プロンプトノードを設定

        Args:
            workflow: ワークフロー辞書
            node_id: ノードID
            prompt_text: プロンプトテキスト
        """
        if node_id not in workflow:
            logger.warning(f"ノードID {node_id} が見つかりません")
            return

        node = workflow[node_id]
        if "inputs" not in node:
            logger.warning(f"ノードID {node_id} に'inputs'がありません")
            return

        node["inputs"]["text"] = prompt_text
        logger.debug(f"プロンプトを設定: ノード {node_id}")

    def _set_sampler(
        self, workflow: Dict[str, Any], node_id: str, sampler: SamplerConfig
    ):
        """
        KSamplerノードを設定

        Args:
            workflow: ワークフロー辞書
            node_id: ノードID
            sampler: サンプラー設定
        """
        if node_id not in workflow:
            logger.warning(f"ノードID {node_id} が見つかりません")
            return

        node = workflow[node_id]
        if "inputs" not in node:
            logger.warning(f"ノードID {node_id} に'inputs'がありません")
            return

        inputs = node["inputs"]
        inputs["steps"] = sampler.steps
        inputs["cfg"] = sampler.cfg
        inputs["sampler_name"] = sampler.sampler_name
        inputs["scheduler"] = sampler.scheduler
        inputs["seed"] = sampler.seed

        logger.debug(f"サンプラーを設定: ノード {node_id}")

    def _set_lora(self, workflow: Dict[str, Any], node_id: str, lora: LoraConfig):
        """
        LoRAノードを設定

        Args:
            workflow: ワークフロー辞書
            node_id: ノードID
            lora: LoRA設定
        """
        if node_id not in workflow:
            logger.warning(f"ノードID {node_id} が見つかりません")
            return

        node = workflow[node_id]
        if "inputs" not in node:
            logger.warning(f"ノードID {node_id} に'inputs'がありません")
            return

        inputs = node["inputs"]
        inputs["lora_name"] = lora.name
        inputs["strength_model"] = lora.model_strength
        inputs["strength_clip"] = lora.clip_strength

        logger.debug(f"LoRAを設定: ノード {node_id}")

    def set_filename_prefix(self, workflow: Dict[str, Any], prefix: str):
        """
        保存ファイル名のプレフィックスを設定

        Args:
            workflow: ワークフロー辞書
            prefix: ファイル名プレフィックス
        """
        node_id = self.config.node_mapping.save_image

        if node_id not in workflow:
            logger.warning(f"保存ノードID {node_id} が見つかりません")
            return

        node = workflow[node_id]
        if "inputs" not in node:
            logger.warning(f"ノードID {node_id} に'inputs'がありません")
            return

        node["inputs"]["filename_prefix"] = prefix
        logger.debug(f"ファイル名プレフィックスを設定: {prefix}")

    # ====== ユーティリティ ======

    def validate_workflow(self, workflow: Dict[str, Any]) -> bool:
        """
        ワークフローが必要なノードを持っているか検証

        Args:
            workflow: ワークフロー辞書

        Returns:
            bool: 有効ならTrue
        """
        node_mapping = self.config.node_mapping
        required_nodes = [
            node_mapping.positive_prompt,
            node_mapping.negative_prompt,
            node_mapping.ksampler,
            node_mapping.lora,
            node_mapping.save_image,
        ]

        missing_nodes = []
        for node_id in required_nodes:
            if node_id not in workflow:
                missing_nodes.append(node_id)

        if missing_nodes:
            logger.error(f"ワークフローに必要なノードがありません: {missing_nodes}")
            return False

        logger.info("ワークフローの検証に成功しました")
        return True

    def save_workflow(self, workflow: Dict[str, Any], output_path: Path):
        """
        ワークフローをJSONファイルに保存

        Args:
            workflow: ワークフロー辞書
            output_path: 出力パス
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(workflow, f, ensure_ascii=False, indent=2)
            logger.info(f"ワークフローを保存しました: {output_path}")
        except Exception as e:
            logger.error(f"ワークフローの保存に失敗しました: {e}")
            raise

    def get_node_info(self, workflow: Dict[str, Any], node_id: str) -> Optional[Dict]:
        """
        特定のノード情報を取得

        Args:
            workflow: ワークフロー辞書
            node_id: ノードID

        Returns:
            Dict or None: ノード情報
        """
        if node_id in workflow:
            return workflow[node_id]
        logger.warning(f"ノードID {node_id} が見つかりません")
        return None


# ====== 便利な関数 ======


def load_workflow_from_file(json_path: Path) -> Dict[str, Any]:
    """
    ワークフローJSONファイルを直接読み込む

    Args:
        json_path: JSONファイルのパス

    Returns:
        Dict[str, Any]: ワークフロー辞書

    Raises:
        FileNotFoundError: ファイルが存在しない
        json.JSONDecodeError: JSON構文エラー
    """
    if not json_path.exists():
        raise FileNotFoundError(f"ワークフローファイルが見つかりません: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_workflow_manager(workflow_config: WorkflowConfig) -> WorkflowManager:
    """
    WorkflowManagerのファクトリ関数

    Args:
        workflow_config: ワークフロー設定

    Returns:
        WorkflowManager
    """
    return WorkflowManager(workflow_config)


# ====== 使用例 ======


def example_usage():
    """使用例"""
    from comfytools.core_models import (
        GenerationParams,
        LoraConfig,
        NodeMapping,
        SamplerConfig,
        WorkflowConfig,
    )

    # ワークフロー設定を作成
    workflow_config = WorkflowConfig(
        json_path=Path("illust_image.json"),
        node_mapping=NodeMapping.default(),
        output_root=Path("output"),
    )

    # WorkflowManagerを作成
    manager = WorkflowManager(workflow_config)

    # ベースワークフローを検証
    base = manager.get_base_workflow()
    if manager.validate_workflow(base):
        print("ワークフローは有効です")

    # 生成パラメータを作成
    params = GenerationParams(
        positive_prompt="1girl, smile, long hair",
        negative_prompt="bad anatomy, blurry",
        sampler=SamplerConfig(
            steps=20, cfg=7.0, sampler_name="euler", scheduler="karras", seed=12345
        ),
        lora=LoraConfig(
            name="OneBreastOut.safetensors", model_strength=0.0, clip_strength=0.0
        ),
        target_axis_name="hair_style",
    )

    # 設定済みワークフローを作成
    configured = manager.create_configured_workflow(params)

    # ファイル名プレフィックスを設定
    manager.set_filename_prefix(configured, "test_run/img")

    # ワークフローを保存（デバッグ用）
    manager.save_workflow(configured, Path("output/configured_workflow.json"))

    print("設定済みワークフローを作成しました")

    # 特定のノード情報を取得
    ksampler_info = manager.get_node_info(
        configured, manager.config.node_mapping.ksampler
    )
    if ksampler_info:
        print(f"KSampler設定: {ksampler_info['inputs']}")


def example_batch_creation():
    """複数のワークフローを作成する例"""
    from comfytools.core_models import (
        GenerationParams,
        LoraConfig,
        NodeMapping,
        SamplerConfig,
        WorkflowConfig,
    )

    workflow_config = WorkflowConfig(
        json_path=Path("illust_image.json"),
        node_mapping=NodeMapping.default(),
        output_root=Path("output"),
    )

    manager = WorkflowManager(workflow_config)

    # 複数のパラメータセット
    prompts = [
        "1girl, smile, long hair",
        "1girl, serious, short hair",
        "1girl, happy, twin tails",
    ]

    workflows = []
    for i, prompt in enumerate(prompts):
        params = GenerationParams(
            positive_prompt=prompt,
            negative_prompt="bad anatomy",
            sampler=SamplerConfig(
                steps=20,
                cfg=7.0,
                sampler_name="euler",
                scheduler="karras",
                seed=1000 + i,
            ),
            lora=LoraConfig(
                name="test.safetensors", model_strength=0.0, clip_strength=0.0
            ),
            target_axis_name="expression",
        )

        workflow = manager.create_configured_workflow(params)
        manager.set_filename_prefix(workflow, f"batch_{i + 1}/img")
        workflows.append(workflow)

    print(f"{len(workflows)} 個のワークフローを作成しました")


if __name__ == "__main__":
    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    example_usage()
    # example_batch_creation()
