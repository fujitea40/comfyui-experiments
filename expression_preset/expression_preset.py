import os
import json
from typing import Any, Dict, Tuple


# -----------------------------------------------------------------------------
# YAML preset loading (optional)
# - Place a YAML file next to this .py file (default: expression_presets.yaml)
# - If PyYAML isn't installed or YAML is missing/invalid, falls back to defaults
# -----------------------------------------------------------------------------
try:
    import yaml  # type: ignore
except Exception:
    yaml = None


DEFAULT_PRESETS: Dict[str, Any] = {
    "defaults": {
        "params": {
            "steps": 25,
            "cfg": 8.0,
            "denoise": 0.48,
        }
    },
    "expressions": {
        "neutral": {
            "expr_prompt": (
                "neutral expression, calm face, relaxed mouth, eyes open, relaxed eyes, "
                "emotionless, natural look, same eye color, consistent eye color"
            ),
            "params": {"denoise": 0.28},
        },
        "smile": {
            "expr_prompt": (
                "gentle smile, soft smile, slightly curved mouth, happy but calm expression, "
                "eyes relaxed"
            ),
        },
        "big_smile_closed_eyes": {
            "expr_prompt": (
                "big smile, joyful expression, eyes closed, smiling eyes, wide curved mouth, "
                "cheerful, very happy expression, slightly raised cheeks"
            ),
        },
        "angry": {
            "expr_prompt": "angry expression, furrowed eyebrows, sharp eyes, tight mouth",
            "params": {"cfg": 7.0, "denoise": 0.30},
        },
        "sad": {
            "expr_prompt": "sad expression, downcast eyes, slightly trembling lips, teary eyes",
        },
        "surprised": {
            "expr_prompt": "surprised expression, wide eyes, slightly open mouth, raised eyebrows",
            "params": {"cfg": 7.0, "denoise": 0.30},
        },
        "embarrassed": {
            "expr_prompt": "embarrassed expression, blushing cheeks, awkward smile, eyes slightly averted",
        },
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Return a merged copy of base updated with override (dicts merged recursively)."""
    out: Dict[str, Any] = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)  # type: ignore[arg-type]
        else:
            out[k] = v
    return out


def _normalize_yaml_schema(data: Any) -> Dict[str, Any]:
    """Accept both schemas:

    1) Recommended:
       defaults: {params:{...}}
       expressions:
         neutral: {expr_prompt:..., params:{...}}

    2) Minimal/legacy-like:
       neutral: {expr_prompt:..., params:{...}}
       smile:   {expr_prompt:..., params:{...}}
    """
    if not isinstance(data, dict):
        raise ValueError("YAML root must be a mapping (dict)")

    if "expressions" in data:
        defaults = data.get("defaults") or {}
        expressions = data.get("expressions") or {}
    else:
        defaults = {}
        expressions = data

    if not isinstance(defaults, dict):
        raise ValueError("'defaults' must be a mapping (dict)")
    if not isinstance(expressions, dict):
        raise ValueError("'expressions' must be a mapping (dict)")

    return {"defaults": defaults, "expressions": expressions}


def _validate_and_compose_presets(presets: Dict[str, Any]) -> Dict[str, Any]:
    """Validate presets and produce a fully-composed structure:

    {
      'expressions': {
         name: {'expr_prompt': str, 'params': {'steps':int,'cfg':float,'denoise':float}}
      }
    }
    """
    defaults_params = (presets.get("defaults") or {}).get("params") or {}
    if defaults_params is None:
        defaults_params = {}

    if not isinstance(defaults_params, dict):
        raise ValueError("defaults.params must be a mapping (dict)")

    expressions = presets.get("expressions") or {}
    if not isinstance(expressions, dict):
        raise ValueError("expressions must be a mapping (dict)")

    composed: Dict[str, Any] = {"expressions": {}}

    for name, conf in expressions.items():
        if not isinstance(name, str) or not name.strip():
            continue
        if not isinstance(conf, dict):
            raise ValueError(f"expression '{name}' must be a mapping (dict)")

        expr_prompt = conf.get("expr_prompt")
        if not isinstance(expr_prompt, str) or not expr_prompt.strip():
            raise ValueError(
                f"expression '{name}' is missing a non-empty 'expr_prompt'"
            )

        merged_params = _deep_merge(defaults_params, conf.get("params") or {})
        if not isinstance(merged_params, dict):
            raise ValueError(f"expression '{name}'.params must be a mapping (dict)")

        # Required params: steps, cfg, denoise
        if (
            "steps" not in merged_params
            or "cfg" not in merged_params
            or "denoise" not in merged_params
        ):
            raise ValueError(
                f"expression '{name}' params must include steps/cfg/denoise (use defaults.params to avoid repetition)"
            )

        try:
            steps = int(merged_params["steps"])
            cfg = float(merged_params["cfg"])
            denoise = float(merged_params["denoise"])
        except Exception as e:
            raise ValueError(f"expression '{name}' has invalid param types: {e}")

        composed["expressions"][name] = {
            "expr_prompt": expr_prompt.strip(),
            "params": {"steps": steps, "cfg": cfg, "denoise": denoise},
        }

    if not composed["expressions"]:
        raise ValueError("No valid expressions found in presets")

    return composed


class ExpressionPresetNode:
    # --- YAML settings ---
    YAML_FILENAME = "expression_presets.yaml"

    # cache
    _CACHE_MTIME: float = -1.0
    _CACHE_PRESETS: Dict[str, Any] = {}

    @classmethod
    def _yaml_path(cls) -> str:
        return os.path.join(os.path.dirname(__file__), cls.YAML_FILENAME)

    @classmethod
    def _load_presets(cls) -> Dict[str, Any]:
        """Load presets with caching. Falls back to DEFAULT_PRESETS on errors."""
        path = cls._yaml_path()

        # If YAML lib isn't available, just use defaults.
        if yaml is None:
            if not cls._CACHE_PRESETS:
                print(
                    "[ExpressionPresetNode] PyYAML not found. Using built-in defaults."
                )
                cls._CACHE_PRESETS = _validate_and_compose_presets(DEFAULT_PRESETS)
                cls._CACHE_MTIME = -1.0
            return cls._CACHE_PRESETS

        # If file doesn't exist, use defaults.
        if not os.path.exists(path):
            if not cls._CACHE_PRESETS:
                print(
                    f"[ExpressionPresetNode] YAML not found: {path}. Using built-in defaults."
                )
                cls._CACHE_PRESETS = _validate_and_compose_presets(DEFAULT_PRESETS)
                cls._CACHE_MTIME = -1.0
            return cls._CACHE_PRESETS

        # Reload only if changed.
        try:
            mtime = os.path.getmtime(path)
        except Exception:
            mtime = -1.0

        if cls._CACHE_PRESETS and mtime == cls._CACHE_MTIME:
            return cls._CACHE_PRESETS

        # Try load
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f)

            normalized = _normalize_yaml_schema(raw)
            merged = _deep_merge(
                DEFAULT_PRESETS, normalized
            )  # allow overriding defaults/expressions
            composed = _validate_and_compose_presets(merged)

            cls._CACHE_PRESETS = composed
            cls._CACHE_MTIME = mtime
            print(f"[ExpressionPresetNode] Loaded presets from YAML: {path}")
            return cls._CACHE_PRESETS

        except Exception as e:
            print(
                f"[ExpressionPresetNode] Failed to load YAML presets ({path}): {e}. Using built-in defaults."
            )
            cls._CACHE_PRESETS = _validate_and_compose_presets(DEFAULT_PRESETS)
            cls._CACHE_MTIME = -1.0
            return cls._CACHE_PRESETS

    @classmethod
    def INPUT_TYPES(cls):
        presets = cls._load_presets()
        expressions = list((presets.get("expressions") or {}).keys())

        # safe fallback
        if not expressions:
            expressions = list((DEFAULT_PRESETS.get("expressions") or {}).keys())

        return {
            "required": {
                "common_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "1girl, anime style, clean lineart, consistent proportions, high quality, character illustration",
                    },
                ),
                "expression": (expressions,),
            }
        }

    # まとめたprompt文字列 + cfg/denoise/steps に加えて、バッチ実行向けのメタ情報も返す
    # 先頭4つ（prompt/cfg/denoise/steps）は既存互換のため順序維持
    RETURN_TYPES = ("STRING", "FLOAT", "FLOAT", "INT", "STRING", "STRING", "STRING")
    RETURN_NAMES = (
        "prompt",
        "cfg",
        "denoise",
        "steps",
        "expression",
        "expr_prompt",
        "meta_json",
    )

    FUNCTION = "run"
    CATEGORY = "Expression"

    def run(
        self, common_prompt: str, expression: str
    ) -> Tuple[str, float, float, int, str, str, str]:
        presets = self.__class__._load_presets()
        expressions: Dict[str, Any] = presets.get("expressions") or {}

        if expression not in expressions:
            # fallback to neutral if exists, otherwise first key
            expression = (
                "neutral"
                if "neutral" in expressions
                else next(iter(expressions.keys()))
            )

        preset = expressions[expression]
        expr_prompt = preset.get("expr_prompt", "")
        params = preset.get("params") or {}

        # 共通部＋表情差分を安全に結合（空行・前後空白も吸収）
        base = (common_prompt or "").strip().strip(",")
        diff = (expr_prompt or "").strip().strip(",")

        if base and diff:
            combined = f"{base}, {diff}"
        else:
            combined = base or diff

        # type-safe outputs
        cfg = float(params.get("cfg"))
        denoise = float(params.get("denoise"))
        steps = int(params.get("steps"))

        meta = {
            "schema": "expression_preset_v1",
            "expression": expression,
            "common_prompt": base,
            "expr_prompt": diff,
            "combined_prompt": combined,
            "params": {"steps": steps, "cfg": cfg, "denoise": denoise},
        }
        meta_json = json.dumps(meta, ensure_ascii=False, sort_keys=True)

        return (combined, cfg, denoise, steps, expression, diff, meta_json)
