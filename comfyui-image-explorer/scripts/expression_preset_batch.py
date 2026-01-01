# scripts/expression_preset_batch.py

from __future__ import annotations

import argparse
import json
import logging

# src を import パスに追加（scripts直叩き用）
import sys
from pathlib import Path
from typing import Iterable, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comfytools.comfyui_client import ComfyUIClient
from comfytools.utils import (
    ensure_directory,
    generate_run_id,
    generate_seed,
    safe_filename,
    setup_logging,
)
from dtrace_loging.logging.trace import trace_io
from expression_preset_batch.config.config_loader import (
    quick_load,
)
from expression_preset_batch.config.workflow import (
    EPBWorkflowManager,
)
from expression_preset_batch.models import (
    GenerationParams,
)

logger = logging.getLogger(__name__)


DEFAULT_EXTS = [".png", ".jpg", ".jpeg", ".webp"]


@trace_io(level=logging.DEBUG)
def iter_image_files(
    images_dir: Path, *, recursive: bool, exts: List[str]
) -> Iterable[Path]:
    exts_norm = {e.lower() for e in exts}
    if recursive:
        for p in images_dir.rglob("*"):
            if p.is_file() and p.suffix.lower() in exts_norm:
                yield p
    else:
        for p in images_dir.iterdir():
            if p.is_file() and p.suffix.lower() in exts_norm:
                yield p


@trace_io(level=logging.DEBUG)
def compute_seed(strategy: str, base: int, index: int) -> int:
    if strategy == "time":
        return int(generate_seed())
    if strategy == "fixed":
        return int(base)
    # increment
    return int(base) + int(index)


@trace_io(level=logging.DEBUG)
def render_prefix(
    template: str, *, image_stem: str, expr: str, run_id: str, seed: int
) -> str:
    # 使える変数: {image} {expr} {run} {seed}
    return template.format(
        image=safe_filename(image_stem),
        expr=safe_filename(expr),
        run=safe_filename(run_id),
        seed=seed,
    )


@trace_io(level=logging.DEBUG)
def write_meta_json(path: Path, meta: dict) -> None:
    ensure_directory(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2, sort_keys=True)


@trace_io(level=logging.DEBUG)
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="ExpressionPresetNode-based batch runner for ComfyUI"
    )
    p.add_argument(
        "-c",
        "--config",
        type=str,
        default="config/epb.yaml",
        help="Config YAML/JSON path",
    )
    p.add_argument(
        "-i", "--images-dir", type=str, required=True, help="Input images directory"
    )
    p.add_argument("--recursive", action="store_true", help="Search images recursively")
    p.add_argument(
        "--limit", type=int, default=0, help="Process only first N images (0=all)"
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not call ComfyUI API (show planned actions)",
    )
    p.add_argument("--verbose", action="store_true", help="Enable debug logging")
    p.add_argument("--log-file", type=Path, help="ログをファイルに出力")
    return p.parse_args()


@trace_io(level=logging.DEBUG)
def main() -> int:
    args = parse_args()
    # ロギング設定（ルートロガーを設定）
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(level=log_level, log_file=args.log_file)
    # setup_logging(debug=args.verbose)

    config_path = Path(args.config).resolve()
    images_dir = Path(args.images_dir).resolve()

    if not images_dir.exists() or not images_dir.is_dir():
        logger.error("images-dir not found or not a directory: %s", images_dir)
        return 2

    cfg = quick_load(config_path)

    run = cfg["run"]
    wfref = cfg["workflow"]
    input_image_cfg = cfg["input_image"]
    expr_mapping = cfg["expression_preset"]
    expressions = cfg["expressions"]
    save_image_cfg = cfg["save_image"]
    seed_node_cfg = cfg["seed_node"]

    client = ComfyUIClient(base_url=run.comfy_url)

    if not client.is_alive():
        logger.error("ComfyUI is not reachable: %s", run.comfy_url)
        return 3

    mgr = EPBWorkflowManager(
        workflow_json=wfref.workflow_json,
        expression_node=expr_mapping,
        input_image_node_id=input_image_cfg["node_id"],
        input_image_input_name=input_image_cfg.get("input_name", "image"),
        save_image_node_id=save_image_cfg.get("node_id"),
        seed_node_id=seed_node_cfg.get("node_id"),
        seed_input_name=seed_node_cfg.get("input_name", "seed") or "seed",
    )

    exts = DEFAULT_EXTS
    files = list(iter_image_files(images_dir, recursive=args.recursive, exts=exts))
    if args.limit and args.limit > 0:
        files = files[: args.limit]

    if not files:
        logger.warning("No image files found in %s", images_dir)
        return 0

    logger.info(
        "Found %d images. expressions=%d repeats=%d",
        len(files),
        len(expressions),
        run.repeats,
    )

    seed_counter = 0

    for img_path in files:
        image_stem = img_path.stem
        logger.info("=== Image: %s ===", img_path.name)

        # 1) upload（必要なら）
        if input_image_cfg.get("upload", True):
            if args.dry_run:
                uploaded_name = img_path.name
                logger.info("[dry-run] upload_image: %s -> %s", img_path, uploaded_name)
            else:
                resp = client.upload_image(
                    img_path,
                    name=None,  # Noneなら元ファイル名
                    image_type=input_image_cfg.get("upload_type", "input"),
                    subfolder=input_image_cfg.get("upload_subfolder", ""),
                    overwrite=bool(input_image_cfg.get("overwrite", False)),
                )
                if not resp.success:
                    logger.error("upload failed: %s", resp.error_message)
                    continue
                uploaded_name = resp.data.get("name")
                if not uploaded_name:
                    logger.error("upload response missing name: %s", resp.data)
                    continue
        else:
            # ComfyUIサーバ側 input/ に既に存在している前提
            uploaded_name = img_path.name

        # 2) expression loop
        for expr in expressions:
            for r in range(run.repeats):
                run_id = generate_run_id()
                seed = compute_seed(run.seed_strategy, run.seed_base, seed_counter)
                seed_counter += 1

                prefix_template = (
                    save_image_cfg.get("filename_prefix_template")
                    or "{image}/{expr}/{run}/img"
                )
                filename_prefix = render_prefix(
                    prefix_template,
                    image_stem=image_stem,
                    expr=expr,
                    run_id=run_id,
                    seed=seed,
                )

                params = GenerationParams(
                    expression=expr,
                    seed=seed,
                    filename_prefix=filename_prefix,
                )

                meta = {
                    "tool": "expression_preset_batch",
                    "input": {
                        "local_path": str(img_path),
                        "uploaded_name": uploaded_name,
                    },
                    "expression": expr,
                    "repeat_index": r,
                    "seed": seed,
                    "filename_prefix": filename_prefix,
                    "workflow_json": str(wfref.workflow_json),
                }

                # メタ保存先（ローカル側のログ/再実行用）
                meta_dir = (
                    Path(cfg["output_root"])
                    / safe_filename(image_stem)
                    / safe_filename(expr)
                    / safe_filename(run_id)
                )
                meta_path = meta_dir / "meta.json"

                if args.dry_run:
                    logger.info(
                        "[dry-run] would run: expr=%s seed=%s prefix=%s",
                        expr,
                        seed,
                        filename_prefix,
                    )
                    write_meta_json(meta_path, {**meta, "dry_run": True})
                    continue

                # workflow生成（B案: 入力画像/expr/seed/prefix を workflow.py が反映）
                workflow = mgr.create_workflow(
                    params, input_image_filename=uploaded_name
                )

                # 実行
                result = client.execute_and_wait(
                    workflow=workflow,
                    poll_interval=run.poll_interval,
                    max_wait_time=run.timeout_sec,
                )

                meta["success"] = bool(result.success)
                if result.success:
                    meta["history"] = (
                        result.data
                    )  # /history のレスポンス（サイズが大きい場合は要注意）
                    logger.info("done: expr=%s seed=%s", expr, seed)
                else:
                    meta["error"] = result.error_message
                    logger.error(
                        "failed: expr=%s seed=%s err=%s",
                        expr,
                        seed,
                        result.error_message,
                    )

                write_meta_json(meta_path, meta)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
