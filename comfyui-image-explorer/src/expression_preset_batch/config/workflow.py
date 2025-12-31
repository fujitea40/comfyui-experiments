# src/expression_preset_batch/config/workflow.py

from __future__ import annotations

import copy
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from expression_preset_batch.models import ExpressionPresetNodeMapping, GenerationParams

logger = logging.getLogger(__name__)

Workflow = Dict[str, Any]


def load_workflow_from_file(json_path: Path) -> Workflow:
    if not json_path.exists():
        raise FileNotFoundError(f"Workflow JSON not found: {json_path}")

    try:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Workflow JSON parse error: {json_path}: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"Workflow JSON root must be dict: {json_path}")

    return data


@dataclass
class EPBWorkflowManager:
    """
    expression_preset_batch 用 Workflow Manager（拡張版・B案）

    - ベースworkflowをロードして保持
    - 実行毎に deepcopy して投入用workflowを作る
    - 差し替え対象:
        1) 入力画像（LoadImage等）: inputs[input_image_input_name]
        2) ExpressionPresetNode: inputs[expression_input_name]
        3) seed（任意）: inputs[seed_input_name]
        4) SaveImage filename_prefix（任意）: inputs["filename_prefix"]

    安全策:
    - 差し替え対象の inputs[...] が list（リンク）なら上書きしない（warnしてスキップ）
    """

    workflow_json: Path
    expression_node: ExpressionPresetNodeMapping

    input_image_node_id: str
    input_image_input_name: str = "image"

    save_image_node_id: Optional[str] = None
    seed_node_id: Optional[str] = None
    seed_input_name: str = "seed"

    def __post_init__(self) -> None:
        self.base_workflow: Workflow = load_workflow_from_file(self.workflow_json)
        self.validate(self.base_workflow)

    def get_base_workflow(self) -> Workflow:
        return copy.deepcopy(self.base_workflow)

    def create_workflow(
        self, params: GenerationParams, *, input_image_filename: str
    ) -> Workflow:
        wf = self.get_base_workflow()

        # 1) 入力画像
        self.set_input_image_filename(wf, input_image_filename)

        # 2) expression
        self.apply_expression(wf, params.expression)

        # 3) seed（設定がある場合のみ）
        if self.seed_node_id is not None:
            self.set_seed(wf, params.seed)

        # 4) filename_prefix（設定がある場合のみ）
        if self.save_image_node_id is not None:
            self.set_filename_prefix(wf, params.filename_prefix)

        return wf

    def set_input_image_filename(self, workflow: Workflow, filename: str) -> None:
        node = self.get_node_info(workflow, self.input_image_node_id)
        if node is None:
            logger.warning(
                "Input image node not found. node_id=%s", self.input_image_node_id
            )
            return

        inputs = node.get("inputs")
        if not isinstance(inputs, dict):
            logger.warning(
                "Input image node inputs invalid. node_id=%s", self.input_image_node_id
            )
            return

        key = self.input_image_input_name
        existing = inputs.get(key)

        if isinstance(existing, list):
            logger.warning(
                "Skip overwriting input image because it is a link(list). "
                "node_id=%s input=%s existing=%r",
                self.input_image_node_id,
                key,
                existing,
            )
            return

        inputs[key] = filename

    def apply_expression(self, workflow: Workflow, expression: str) -> None:
        node = self.get_node_info(workflow, self.expression_node.node_id)
        if node is None:
            logger.warning(
                "Expression node not found. node_id=%s", self.expression_node.node_id
            )
            return

        inputs = node.get("inputs")
        if not isinstance(inputs, dict):
            logger.warning(
                "Expression node inputs invalid. node_id=%s",
                self.expression_node.node_id,
            )
            return

        key = self.expression_node.expression_input_name
        existing = inputs.get(key)

        if isinstance(existing, list):
            logger.warning(
                "Skip overwriting expression because it is a link(list). "
                "node_id=%s input=%s existing=%r",
                self.expression_node.node_id,
                key,
                existing,
            )
            return

        inputs[key] = expression

    def set_seed(self, workflow: Workflow, seed: int) -> None:
        if not self.seed_node_id:
            return

        node = self.get_node_info(workflow, self.seed_node_id)
        if node is None:
            logger.warning("Seed node not found. node_id=%s", self.seed_node_id)
            return

        inputs = node.get("inputs")
        if not isinstance(inputs, dict):
            logger.warning("Seed node inputs invalid. node_id=%s", self.seed_node_id)
            return

        key = self.seed_input_name
        existing = inputs.get(key)

        if isinstance(existing, list):
            logger.warning(
                "Skip overwriting seed because it is a link(list). "
                "node_id=%s input=%s existing=%r",
                self.seed_node_id,
                key,
                existing,
            )
            return

        inputs[key] = int(seed)

    def set_filename_prefix(self, workflow: Workflow, prefix: str) -> None:
        if not self.save_image_node_id:
            return

        node = self.get_node_info(workflow, self.save_image_node_id)
        if node is None:
            logger.warning(
                "SaveImage node not found. node_id=%s", self.save_image_node_id
            )
            return

        inputs = node.get("inputs")
        if not isinstance(inputs, dict):
            logger.warning(
                "SaveImage node inputs invalid. node_id=%s", self.save_image_node_id
            )
            return

        existing = inputs.get("filename_prefix")
        if isinstance(existing, list):
            logger.warning(
                "Skip overwriting filename_prefix because it is a link(list). "
                "node_id=%s existing=%r",
                self.save_image_node_id,
                existing,
            )
            return

        inputs["filename_prefix"] = prefix

    def validate(self, workflow: Optional[Workflow] = None) -> bool:
        wf = workflow if workflow is not None else self.base_workflow
        ok = True

        # input image
        if self.get_node_info(wf, self.input_image_node_id) is None:
            logger.error(
                "Input image node missing: node_id=%s", self.input_image_node_id
            )
            ok = False

        # expression
        expr_node = self.get_node_info(wf, self.expression_node.node_id)
        if expr_node is None:
            logger.error(
                "Expression node missing: node_id=%s", self.expression_node.node_id
            )
            ok = False

        # save image (optional)
        if (
            self.save_image_node_id
            and self.get_node_info(wf, self.save_image_node_id) is None
        ):
            logger.error("SaveImage node missing: node_id=%s", self.save_image_node_id)
            ok = False

        # seed (optional)
        if self.seed_node_id and self.get_node_info(wf, self.seed_node_id) is None:
            logger.error("Seed node missing: node_id=%s", self.seed_node_id)
            ok = False

        return ok

    def save_workflow(self, workflow: Workflow, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(workflow, f, ensure_ascii=False, indent=2)

    @staticmethod
    def get_node_info(workflow: Workflow, node_id: str) -> Optional[Dict[str, Any]]:
        node = workflow.get(node_id)
        if node is None:
            return None
        if not isinstance(node, dict):
            logger.warning(
                "Node is not a dict. node_id=%s type=%s", node_id, type(node)
            )
            return None
        return node
