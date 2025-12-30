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


Workflow: type = Dict[str, Any]


def load_workflow_from_file(json_path: Path) -> Workflow:
    """
    ComfyUIの workflow(prompt) 形式JSONを読み込む。
    """
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
    expression_preset_batch 用 Workflow Manager（最小構成）

    方針:
    - ベースworkflowをロードして保持
    - 実行毎に deepcopy して投入用workflowを作る
    - 差し替えるのは
        1) ExpressionPresetNode の expression入力
        2) SaveImage の filename_prefix（任意）
      のみ
    - 入力が list（リンク）になっている場合はリンク破壊を避けるため上書きしない
    """

    workflow_json: Path
    expression_node: ExpressionPresetNodeMapping
    save_image_node_id: Optional[str] = None

    def __post_init__(self) -> None:
        self.base_workflow: Workflow = self._load_workflow()
        # 起動時点で最低限の検証（厳しすぎると困るのでwarn中心）
        self.validate(self.base_workflow)

    def _load_workflow(self) -> Workflow:
        return load_workflow_from_file(self.workflow_json)

    def get_base_workflow(self) -> Workflow:
        """
        ベースworkflowの deepcopy を返す（呼び出し側で安全に編集可能）
        """
        return copy.deepcopy(self.base_workflow)

    def create_workflow(self, params: GenerationParams) -> Workflow:
        """
        params を反映した投入用workflowを生成して返す。
        """
        wf = self.get_base_workflow()

        # expression の適用（必須）
        self.apply_expression(wf, params.expression)

        # filename_prefix（任意）
        if self.save_image_node_id is not None:
            self.set_filename_prefix(wf, params.filename_prefix)

        return wf

    def apply_expression(self, workflow: Workflow, expression: str) -> None:
        """
        ExpressionPresetNode の inputs[expression_input_name] に expression を設定する。

        安全策:
        - 対象inputsが list（リンク）なら上書きせずwarnしてスキップ
        """
        node = self.get_node_info(workflow, self.expression_node.node_id)
        if node is None:
            logger.warning(
                "Expression node not found. node_id=%s", self.expression_node.node_id
            )
            return

        inputs = node.get("inputs")
        if not isinstance(inputs, dict):
            logger.warning(
                "Expression node has no valid inputs dict. node_id=%s",
                self.expression_node.node_id,
            )
            return

        key = self.expression_node.expression_input_name
        existing = inputs.get(key)

        if isinstance(existing, list):
            logger.warning(
                "Skip overwriting expression input because it is a link(list). "
                "node_id=%s input=%s existing=%r",
                self.expression_node.node_id,
                key,
                existing,
            )
            return

        inputs[key] = expression

    def set_filename_prefix(self, workflow: Workflow, prefix: str) -> None:
        """
        SaveImage ノードの inputs['filename_prefix'] を設定する（任意）。

        安全策:
        - 既存値が list（リンク）なら上書きしない
        """
        if not self.save_image_node_id:
            return

        node = self.get_node_info(workflow, self.save_image_node_id)
        if node is None:
            logger.warning("SaveImage node not found. node_id=%s", self.save_image_node_id)
            return

        inputs = node.get("inputs")
        if not isinstance(inputs, dict):
            logger.warning(
                "SaveImage node has no valid inputs dict. node_id=%s",
                self.save_image_node_id,
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
        """
        workflowの最低限検証。

        - expressionノードが存在するか
        - inputsがdictか
        - SaveImage指定時は SaveImageノードが存在するか

        NOTE:
        - expression_input_name が inputs に「存在しない」ケースでも、ComfyUIのノードは
          inputs辞書に任意キーを追加して動く場合があるため、ここではwarnに留める。
        """
        wf = workflow if workflow is not None else self.base_workflow
        ok = True

        expr_node = self.get_node_info(wf, self.expression_node.node_id)
        if expr_node is None:
            logger.error("Expression node missing: node_id=%s", self.expression_node.node_id)
            ok = False
        else:
            inputs = expr_node.get("inputs")
            if not isinstance(inputs, dict):
                logger.error(
                    "Expression node inputs invalid (not dict): node_id=%s",
                    self.expression_node.node_id,
                )
                ok = False
            else:
                key = self.expression_node.expression_input_name
                if key not in inputs:
                    logger.warning(
                        "Expression input key not found in inputs (will be added on apply). "
                        "node_id=%s input=%s",
                        self.expression_node.node_id,
                        key,
                    )

        if self.save_image_node_id:
            save_node = self.get_node_info(wf, self.save_image_node_id)
            if save_node is None:
                logger.error("SaveImage node missing: node_id=%s", self.save_image_node_id)
                ok = False
            else:
                inputs = save_node.get("inputs")
                if not isinstance(inputs, dict):
                    logger.error(
                        "SaveImage node inputs invalid (not dict): node_id=%s",
                        self.save_image_node_id,
                    )
                    ok = False

        return ok

    def save_workflow(self, workflow: Workflow, path: Path) -> None:
        """
        デバッグ用にworkflow JSONを保存する。
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(workflow, f, ensure_ascii=False, indent=2)

    @staticmethod
    def get_node_info(workflow: Workflow, node_id: str) -> Optional[Dict[str, Any]]:
        """
        指定 node_id のノード辞書を返す。無ければ None。
        """
        node = workflow.get(node_id)
        if node is None:
            return None
        if not isinstance(node, dict):
            logger.warning("Node is not a dict. node_id=%s type=%s", node_id, type(node))
            return None
        return node


def create_workflow_manager(
    workflow_json: Path,
    expression_node: ExpressionPresetNodeMapping,
    save_image_node_id: Optional[str] = None,
) -> EPBWorkflowManager:
    """
    EPBWorkflowManager の薄いファクトリ
    """
    return EPBWorkflowManager(
        workflow_json=workflow_json,
        expression_node=expression_node,
        save_image_node_id=save_image_node_id,
    )
