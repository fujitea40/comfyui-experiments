from __future__ import annotations

import functools
import inspect
import logging
import time
from typing import Any, Callable, Optional, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def _default_mask(value: Any) -> Any:  # pylint: disable=missing-trace-io
    # 必要に応じて拡張：パスワード・トークン等を伏せる
    return value


def trace_io(  # pylint: disable=missing-trace-io
    *,
    logger: Optional[logging.Logger] = None,
    level: int = logging.DEBUG,
    mask: Callable[[Any], Any] = _default_mask,
    log_return: bool = True,
    include_args: bool = True,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    関数の入出力・所要時間・例外をログ出力するデコレータ。

    - logger未指定なら、関数の属するモジュール名で取得
    - maskで引数/戻り値をマスク可能
    - async関数にも対応
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        _logger = logger or logging.getLogger(func.__module__)
        qualname = f"{func.__module__}.{getattr(func, '__qualname__', func.__name__)}"
        is_async = inspect.iscoroutinefunction(func)

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                start = time.perf_counter()
                if _logger.isEnabledFor(level):
                    payload = (
                        {"args": mask(args), "kwargs": mask(kwargs)}
                        if include_args
                        else {}
                    )
                    _logger.log(level, "START %s %s", qualname, payload)
                try:
                    result = await func(*args, **kwargs)
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    if _logger.isEnabledFor(level):
                        out = {"return": mask(result)} if log_return else {}
                        _logger.log(
                            level, "END   %s %s (%.1fms)", qualname, out, elapsed_ms
                        )
                    return result
                except Exception:
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    _logger.exception("ERR   %s (%.1fms)", qualname, elapsed_ms)
                    raise

            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = time.perf_counter()
            if _logger.isEnabledFor(level):
                payload = (
                    {"args": mask(args), "kwargs": mask(kwargs)} if include_args else {}
                )
                _logger.log(level, "START %s %s", qualname, payload)
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.perf_counter() - start) * 1000
                if _logger.isEnabledFor(level):
                    out = {"return": mask(result)} if log_return else {}
                    _logger.log(
                        level, "END   %s %s (%.1fms)", qualname, out, elapsed_ms
                    )
                return result
            except Exception:
                elapsed_ms = (time.perf_counter() - start) * 1000
                _logger.exception("ERR   %s (%.1fms)", qualname, elapsed_ms)
                raise

        return sync_wrapper

    return decorator
