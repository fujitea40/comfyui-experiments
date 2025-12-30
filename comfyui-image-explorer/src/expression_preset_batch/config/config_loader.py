# src/expression_preset_batch/config/config_loader.py

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from expression_preset_batch.models import ExpressionPresetNodeMapping, normalize_expressions


def load_yaml_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"YAML parse error: {path}: {e}") from e
    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a mapping/dict: {path}")
    return data


def load_json_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f) or {}
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parse error: {path}: {e}") from e
    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a mapping/dict: {path}")
    return data


def _require_str(d: Dict[str, Any], key: str, ctx: str) -> str:
    v = d.get(key)
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"Missing or invalid '{key}' in {ctx}")
    return v.strip()


def _optional_str(d: Dict[str, Any], key: str, default: str) -> str:
    v = d.get(key, default)
    if not isinstance(v, str) or not v.strip():
        return default
    return v.strip()


def _optional_int(d: Dict[str, Any], key: str, default: int) -> int:
    v = d.get(key, default)
    if v is None:
        return default
    if not isinstance(v, int):
        raise ValueError(f"Invalid '{key}' (must be int): {v!r}")
    return v


def _optional_float(d: Dict[str, Any], key: str, default: float) -> float:
    v = d.get(key, default)
    if v is None:
        return default
    if not isinstance(v, (int, float)):
        raise ValueError(f"Invalid '{key}' (must be number): {v!r}")
    return float(v)


def _resolve_path(base_dir: Path, raw: Union[str, Path]) -> Path:
    p = Path(raw) if isinstance(raw, str) else raw
    if p.is_absolute():
        return p
    return (base_dir / p).resolve()


@dataclass(frozen=True)
class EPBWorkflowRef:
    """
    expression_preset_batch が叩く workflow の参照情報。
    既存の WorkflowConfig を流用せず、まずは必要最低限。
    """
    workflow_json: Path
    output_root: Path

    def __post_init__(self) -> None:
        if not self.workflow_json.exists():
            raise FileNotFoundError(f"workflow_json not found: {self.workflow_json}")


@dataclass(frozen=True)
class EPBRunConfig:
    """
    実行環境・実行戦略（seed/回数/待機）の設定。
    既存の ExecutionConfig を流用せず、epb向け最小。
    """
    comfy_url: str
    poll_interval: float = 1.0
    timeout_sec: Optional[float] = 600.0
    repeats: int = 1

    seed_strategy: str = "time"   # "time" | "increment" | "fixed"
    seed_base: int = 0            # seed_strategy="fixed"/"increment"で使用

    def __post_init__(self) -> None:
        if self.repeats <= 0:
            raise ValueError("repeats must be > 0")
        if self.poll_interval <= 0:
            raise ValueError("poll_interval must be > 0")
        if self.timeout_sec is not None and self.timeout_sec <= 0:
            raise ValueError("timeout_sec must be > 0 when specified")
        if self.seed_strategy not in ("time", "increment", "fixed"):
            raise ValueError("seed_strategy must be one of: time, increment, fixed")


class ConfigLoader:
    """
    expression_preset_batch 用の設定ローダ。
    YAML/JSON を読み、epb実行に必要な最小構造へ変換する。

    想定スキーマ（推奨）:
    ---
    comfy_url: "http://127.0.0.1:8188"
    workflow_json: "./workflows/expression_preset_workflow.json"
    output_root: "./outputs"

    expression_preset:
      node_id: "123"
      expression_input_name: "expression"
      expressions:
        - neutral
        - smile
        - wink

    run:
      repeats: 3
      poll_interval: 1.0
      timeout_sec: 600
      seed_strategy: "time"        # time|increment|fixed
      seed_base: 0
    """

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.base_dir = config_path.parent.resolve()

        suffix = config_path.suffix.lower()
        if suffix in (".yaml", ".yml"):
            self.raw = load_yaml_file(config_path)
        elif suffix == ".json":
            self.raw = load_json_file(config_path)
        else:
            raise ValueError(f"Unsupported config type: {config_path}")

    def load_workflow(self) -> EPBWorkflowRef:
        # root 直下優先、なければ workflow セクションも許可
        root = self.raw
        wf = root.get("workflow", {}) if isinstance(root.get("workflow", {}), dict) else {}

        workflow_json_raw = root.get("workflow_json") or wf.get("workflow_json") or wf.get("json_path")
        if not isinstance(workflow_json_raw, str) or not workflow_json_raw.strip():
            raise ValueError("Missing workflow_json (or workflow.workflow_json / workflow.json_path)")

        output_root_raw = root.get("output_root") or wf.get("output_root") or "./outputs"

        workflow_json = _resolve_path(self.base_dir, workflow_json_raw)
        output_root = _resolve_path(self.base_dir, output_root_raw)

        return EPBWorkflowRef(workflow_json=workflow_json, output_root=output_root)

    def load_expression_preset(self) -> Dict[str, Any]:
        sec = self.raw.get("expression_preset")
        if not isinstance(sec, dict):
            raise ValueError("Missing 'expression_preset' section (must be mapping)")

        node_id = _require_str(sec, "node_id", "expression_preset")
        input_name = _optional_str(sec, "expression_input_name", "expression")

        expressions_raw = sec.get("expressions")
        if not isinstance(expressions_raw, list):
            raise ValueError("expression_preset.expressions must be a list of strings")

        expressions = normalize_expressions(expressions_raw)
        if not expressions:
            raise ValueError("expression_preset.expressions must contain at least one expression")

        mapping = ExpressionPresetNodeMapping(node_id=node_id, expression_input_name=input_name)
        mapping.validate()

        return {
            "mapping": mapping,
            "expressions": expressions,
        }

    def load_run(self) -> EPBRunConfig:
        root = self.raw
        run = root.get("run", {}) if isinstance(root.get("run", {}), dict) else {}

        comfy_url = _require_str(root, "comfy_url", "root") if "comfy_url" in root else _require_str(run, "comfy_url", "run")

        repeats = _optional_int(run, "repeats", 1)
        poll_interval = _optional_float(run, "poll_interval", 1.0)

        # Noneを許可（無制限待ち）
        timeout_sec_val = run.get("timeout_sec", 600.0)
        if timeout_sec_val is None:
            timeout_sec = None
        else:
            if not isinstance(timeout_sec_val, (int, float)):
                raise ValueError("run.timeout_sec must be number or null")
            timeout_sec = float(timeout_sec_val)

        seed_strategy = _optional_str(run, "seed_strategy", "time")
        seed_base = _optional_int(run, "seed_base", 0)

        return EPBRunConfig(
            comfy_url=comfy_url,
            poll_interval=poll_interval,
            timeout_sec=timeout_sec,
            repeats=repeats,
            seed_strategy=seed_strategy,
            seed_base=seed_base,
        )

    def load_all(self) -> Dict[str, Any]:
        workflow = self.load_workflow()
        ep = self.load_expression_preset()
        run = self.load_run()

        # output_root は workflow から取り、runner側で使えるようにフラットにも置く
        return {
            "workflow": workflow,
            "run": run,
            "expression_preset": ep["mapping"],
            "expressions": ep["expressions"],
            "output_root": workflow.output_root,
        }


def load_config(config_path: Path) -> ConfigLoader:
    return ConfigLoader(config_path)


def quick_load(config_path: Path) -> Dict[str, Any]:
    return ConfigLoader(config_path).load_all()
