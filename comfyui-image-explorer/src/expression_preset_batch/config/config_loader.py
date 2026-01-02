# src/expression_preset_batch/config/config_loader.py

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from dtrace_loging.logging.trace import trace_io
from expression_preset_batch.models import (
    ExpressionPresetNodeMapping,
    normalize_expressions,
)

logger = logging.getLogger(__name__)


@trace_io(level=logging.DEBUG)
def _optional_str_list(d: Dict[str, Any], key: str, default: List[str]) -> List[str]:
    v = d.get(key, default)
    if v is None:
        return list(default)
    if not isinstance(v, list) or not all(isinstance(x, str) and x.strip() for x in v):
        raise ValueError(f"Invalid '{key}' (must be list[str]): {v!r}")
    return [x.strip() for x in v]


@trace_io(level=logging.DEBUG)
def _optional_num_list(
    d: Dict[str, Any], key: str, default: List[float]
) -> List[float]:
    v = d.get(key, default)
    if v is None:
        return list(default)
    if not isinstance(v, list) or not all(isinstance(x, (int, float)) for x in v):
        raise ValueError(f"Invalid '{key}' (must be list[number]): {v!r}")
    return [float(x) for x in v]


@trace_io(level=logging.DEBUG)
def _resolve_path(base_dir: Path, raw: str) -> Path:
    p = Path(raw)
    if p.is_absolute():
        return p
    return (base_dir / p).resolve()


@trace_io(level=logging.DEBUG)
def _require_str(d: Dict[str, Any], key: str, ctx: str) -> str:
    v = d.get(key)
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"Missing or invalid '{key}' in {ctx}")
    return v.strip()


@trace_io(level=logging.DEBUG)
def _optional_str(d: Dict[str, Any], key: str, default: str) -> str:
    v = d.get(key, default)
    return v.strip() if isinstance(v, str) and v.strip() else default


@trace_io(level=logging.DEBUG)
def _optional_bool(d: Dict[str, Any], key: str, default: bool) -> bool:
    v = d.get(key, default)
    return bool(v) if isinstance(v, bool) else default


@trace_io(level=logging.DEBUG)
def _optional_int(d: Dict[str, Any], key: str, default: int) -> int:
    v = d.get(key, default)
    if v is None:
        return default
    if not isinstance(v, int):
        raise ValueError(f"Invalid '{key}' (must be int): {v!r}")
    return v


@trace_io(level=logging.DEBUG)
def _optional_float(d: Dict[str, Any], key: str, default: float) -> float:
    v = d.get(key, default)
    if v is None:
        return default
    if not isinstance(v, (int, float)):
        raise ValueError(f"Invalid '{key}' (must be number): {v!r}")
    return float(v)


@dataclass(frozen=True)
class EPBWorkflowRef:
    workflow_json: Path
    output_root: Path

    @trace_io(level=logging.DEBUG)
    def __post_init__(self) -> None:
        if not self.workflow_json.exists():
            raise FileNotFoundError(f"workflow_json not found: {self.workflow_json}")


@dataclass(frozen=True)
class EPBRunConfig:
    comfy_url: str
    poll_interval: float = 1.0
    timeout_sec: Optional[float] = 600.0
    repeats: int = 1

    seed_strategy: str = "time"  # time|increment|fixed
    seed_base: int = 0

    @trace_io(level=logging.DEBUG)
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
    推奨スキーマ（例）:

    comfy_url: "http://127.0.0.1:8188"
    workflow_json: "./workflows/epb.json"
    output_root: "./outputs"

    input_image:
      node_id: "10"
      input_name: "image"
      upload: true
      upload_type: "input"
      upload_subfolder: ""
      overwrite: false

    expression_preset:
      node_id: "123"
      expression_input_name: "expression"
      expressions: [neutral, smile, wink]

    save_image:
      node_id: "999"
      filename_prefix_template: "{image}/{expr}/{run}/img"

    seed_node:
      node_id: "6"
      input_name: "seed"

    run:
      repeats: 3
      poll_interval: 1.0
      timeout_sec: 600
      seed_strategy: "time"
      seed_base: 0
    """

    @trace_io(level=logging.DEBUG)
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.base_dir = config_path.parent.resolve()

        if config_path.suffix.lower() in (".yaml", ".yml"):
            with config_path.open("r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
        elif config_path.suffix.lower() == ".json":
            with config_path.open("r", encoding="utf-8") as f:
                raw = json.load(f) or {}
        else:
            raise ValueError(f"Unsupported config type: {config_path}")

        if not isinstance(raw, dict):
            raise ValueError(f"Config root must be dict: {config_path}")

        self.raw: Dict[str, Any] = raw

    @trace_io(level=logging.DEBUG)
    def load_workflow(self) -> EPBWorkflowRef:
        workflow_json_raw = self.raw.get("workflow_json")
        if not isinstance(workflow_json_raw, str) or not workflow_json_raw.strip():
            raise ValueError("Missing workflow_json")

        output_root_raw = self.raw.get("output_root", "./outputs")
        if not isinstance(output_root_raw, str) or not output_root_raw.strip():
            output_root_raw = "./outputs"

        logger.debug("Loaded workflow_json: %s", workflow_json_raw)
        logger.debug("self.base_dir: %s", self.base_dir)
        return EPBWorkflowRef(
            workflow_json=_resolve_path(self.base_dir, workflow_json_raw.strip()),
            output_root=_resolve_path(self.base_dir, output_root_raw.strip()),
        )

    @trace_io(level=logging.DEBUG)
    def load_input_image(self) -> Dict[str, Any]:
        sec = self.raw.get("input_image")
        if not isinstance(sec, dict):
            raise ValueError("Missing 'input_image' section (must be mapping)")

        node_id = _require_str(sec, "node_id", "input_image")
        input_name = _optional_str(sec, "input_name", "image")

        upload = _optional_bool(sec, "upload", True)
        upload_type = _optional_str(sec, "upload_type", "input")
        upload_subfolder = _optional_str(sec, "upload_subfolder", "")
        overwrite = _optional_bool(sec, "overwrite", False)

        return {
            "node_id": node_id,
            "input_name": input_name,
            "upload": upload,
            "upload_type": upload_type,
            "upload_subfolder": upload_subfolder,
            "overwrite": overwrite,
        }

    @trace_io(level=logging.DEBUG)
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
            raise ValueError(
                "expression_preset.expressions must contain at least one expression"
            )

        mapping = ExpressionPresetNodeMapping(
            node_id=node_id, expression_input_name=input_name
        )
        mapping.validate()

        return {"mapping": mapping, "expressions": expressions}

    @trace_io(level=logging.DEBUG)
    def load_save_image(self) -> Dict[str, Any]:
        sec = self.raw.get("save_image", {})
        if sec is None:
            sec = {}
        if not isinstance(sec, dict):
            raise ValueError("save_image must be mapping when specified")

        node_id = sec.get("node_id")
        if node_id is not None and (
            not isinstance(node_id, str) or not node_id.strip()
        ):
            raise ValueError(
                "save_image.node_id must be non-empty string when specified"
            )

        template = _optional_str(
            sec, "filename_prefix_template", "{image}/{expr}/{run}/img"
        )

        return {
            "node_id": node_id.strip() if isinstance(node_id, str) else None,
            "filename_prefix_template": template,
        }

    @trace_io(level=logging.DEBUG)
    def load_seed_node(self) -> Dict[str, Any]:
        sec = self.raw.get("seed_node", {})
        if sec is None:
            sec = {}
        if not isinstance(sec, dict):
            raise ValueError("seed_node must be mapping when specified")

        node_id = sec.get("node_id")
        if node_id is None:
            return {"node_id": None, "input_name": "seed"}

        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError(
                "seed_node.node_id must be non-empty string when specified"
            )

        input_name = _optional_str(sec, "input_name", "seed")
        return {"node_id": node_id.strip(), "input_name": input_name}

    @trace_io(level=logging.DEBUG)
    def load_run(self) -> EPBRunConfig:
        run = self.raw.get("run", {})
        if run is None:
            run = {}
        if not isinstance(run, dict):
            raise ValueError("run must be mapping when specified")

        comfy_url = (
            _require_str(self.raw, "comfy_url", "root")
            if "comfy_url" in self.raw
            else _require_str(run, "comfy_url", "run")
        )
        repeats = _optional_int(run, "repeats", 1)
        poll_interval = _optional_float(run, "poll_interval", 1.0)

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

    @trace_io(level=logging.DEBUG)
    def load_sampler_node(self) -> Dict[str, Any]:
        sec = self.raw.get("sampler_node", {})
        if sec is None:
            sec = {}
        if not isinstance(sec, dict):
            raise ValueError("sampler_node must be mapping when specified")

        node_id = sec.get("node_id")
        if node_id is None:
            # sampler差し替え無効（＝既存挙動）
            return {"node_id": None}

        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError(
                "sampler_node.node_id must be non-empty string when specified"
            )

        return {
            "node_id": node_id.strip(),
            "steps_input": _optional_str(sec, "steps_input", "steps"),
            "cfg_input": _optional_str(sec, "cfg_input", "cfg"),
            "denoise_input": _optional_str(sec, "denoise_input", "denoise"),
            "sampler_name_input": _optional_str(
                sec, "sampler_name_input", "sampler_name"
            ),
            "scheduler_input": _optional_str(sec, "scheduler_input", "scheduler"),
        }

    @trace_io(level=logging.DEBUG)
    def load_sampler_sweep(self) -> Optional[Dict[str, Any]]:
        sec = self.raw.get("sampler_sweep")
        if sec is None:
            return None
        if not isinstance(sec, dict):
            raise ValueError("sampler_sweep must be mapping when specified")

        steps = sec.get("steps")
        cfg = sec.get("cfg")
        denoise = sec.get("denoise")
        sampler = sec.get("sampler")
        scheduler = sec.get("scheduler")

        # “指定されたら必須キーは全部 list で” ルール（取りこぼし事故防止）
        for k, v in [
            ("steps", steps),
            ("cfg", cfg),
            ("denoise", denoise),
            ("sampler", sampler),
            ("scheduler", scheduler),
        ]:
            if not isinstance(v, list) or not v:
                raise ValueError(f"sampler_sweep.{k} must be non-empty list")

        if not all(isinstance(x, int) for x in steps):
            raise ValueError("sampler_sweep.steps must be list[int]")
        if not all(isinstance(x, (int, float)) for x in cfg):
            raise ValueError("sampler_sweep.cfg must be list[number]")
        if not all(isinstance(x, (int, float)) for x in denoise):
            raise ValueError("sampler_sweep.denoise must be list[number]")
        if not all(isinstance(x, str) and x.strip() for x in sampler):
            raise ValueError("sampler_sweep.sampler must be list[str]")
        if not all(isinstance(x, str) and x.strip() for x in scheduler):
            raise ValueError("sampler_sweep.scheduler must be list[str]")

        return {
            "steps": [int(x) for x in steps],
            "cfg": [float(x) for x in cfg],
            "denoise": [float(x) for x in denoise],
            "sampler": [x.strip() for x in sampler],
            "scheduler": [x.strip() for x in scheduler],
        }

    @trace_io(level=logging.DEBUG)
    def load_all(self) -> Dict[str, Any]:
        workflow = self.load_workflow()
        input_image = self.load_input_image()
        ep = self.load_expression_preset()
        save_image = self.load_save_image()
        seed_node = self.load_seed_node()
        sampler_node = self.load_sampler_node()
        sampler_sweep = self.load_sampler_sweep()
        run = self.load_run()

        return {
            "workflow": workflow,
            "run": run,
            "input_image": input_image,
            "expression_preset": ep["mapping"],
            "expressions": ep["expressions"],
            "save_image": save_image,
            "seed_node": seed_node,
            "sampler_node": sampler_node,
            "sampler_sweep": sampler_sweep,
            "output_root": workflow.output_root,
        }


@trace_io(level=logging.DEBUG)
def quick_load(config_path: Path) -> Dict[str, Any]:
    return ConfigLoader(config_path).load_all()
