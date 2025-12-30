"""
comfytools package

複数ツールで共有する末端部品・ComfyUIクライアントをまとめる。

ここでは「利用側がよく使うもの」だけを再exportする。
"""

from __future__ import annotations

try:
    from .comfyui_client import ComfyUIClient, ComfyUIResponse
except Exception:  # pragma: no cover
    ComfyUIClient = None  # type: ignore
    ComfyUIResponse = None  # type: ignore

# core_models.py は移行中に未配置の可能性があるため、強制importはしない
# 必要になったらここに再exportを追加する

__all__ = [
    "ComfyUIClient",
    "ComfyUIResponse",
]

__version__ = "0.1.0"
