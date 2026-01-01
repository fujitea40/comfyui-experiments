from __future__ import annotations

import astroid
from pylint.checkers import BaseChecker

# from pylint.interfaces import IAstroidChecker

# 必須にしたいデコレータ名
REQUIRED_DECORATOR_NAMES = {"trace_io"}

# 対象外にしたい関数名（必要に応じて調整）
EXCLUDED_FUNCTION_NAMES = {
    "__init__",
    "__repr__",
    "__str__",
    "__hash__",
    "__iter__",
    "__enter__",
    "__exit__",
    "__aenter__",
    "__aexit__",
}

# 対象外にしたいデコレータ（@property などは通常ログ不要になりがち）
EXCLUDED_DECORATOR_NAMES = {"property", "cached_property"}


class RequireTraceIOChecker(BaseChecker):
    # __implements__ = IAstroidChecker
    name = "require-trace-io"
    priority = -1

    msgs = {
        "C9101": (
            "Function '%s' must be decorated with @trace_io",
            "missing-trace-io",
            "All functions/methods should include trace logging via @trace_io.",
        )
    }

    def visit_functiondef(self, node: astroid.FunctionDef) -> None:  # pylint: disable=missing-trace-io
        if self._should_skip(node):
            return

        if not self._has_trace_io(node):
            self.add_message("missing-trace-io", node=node, args=(node.name,))

    def visit_asyncfunctiondef(self, node: astroid.AsyncFunctionDef) -> None:  # pylint: disable=missing-trace-io
        if self._should_skip(node):
            return

        if not self._has_trace_io(node):
            self.add_message("missing-trace-io", node=node, args=(node.name,))

    def _should_skip(  # pylint: disable=missing-trace-io
        self, node: astroid.FunctionDef | astroid.AsyncFunctionDef
    ) -> bool:
        # 特殊メソッドなどは除外（必要なら削除）
        if node.name in EXCLUDED_FUNCTION_NAMES:
            return True

        # property / cached_property などは除外（必要なら削除）
        if self._has_any_decorator(node, EXCLUDED_DECORATOR_NAMES):
            return True

        return False

    def _has_any_decorator(  # pylint: disable=missing-trace-io
        self,
        node: astroid.FunctionDef | astroid.AsyncFunctionDef,
        names: set[str],
    ) -> bool:
        if not node.decorators:
            return False

        for dec in node.decorators.nodes:
            # @name
            if isinstance(dec, astroid.Name) and dec.name in names:
                return True
            # @module.name
            if isinstance(dec, astroid.Attribute) and dec.attrname in names:
                return True
            # @name(...)
            if isinstance(dec, astroid.Call):
                func = dec.func
                if isinstance(func, astroid.Name) and func.name in names:
                    return True
                if isinstance(func, astroid.Attribute) and func.attrname in names:
                    return True

        return False

    def _has_trace_io(  # pylint: disable=missing-trace-io
        self, node: astroid.FunctionDef | astroid.AsyncFunctionDef
    ) -> bool:
        if not node.decorators:
            return False

        for dec in node.decorators.nodes:
            # @trace_io
            if isinstance(dec, astroid.Name) and dec.name in REQUIRED_DECORATOR_NAMES:
                return True

            # @trace_io(...)
            if isinstance(dec, astroid.Call) and isinstance(dec.func, astroid.Name):
                if dec.func.name in REQUIRED_DECORATOR_NAMES:
                    return True

            # @module.trace_io
            if (
                isinstance(dec, astroid.Attribute)
                and dec.attrname in REQUIRED_DECORATOR_NAMES
            ):
                return True

            # @module.trace_io(...)
            if isinstance(dec, astroid.Call) and isinstance(
                dec.func, astroid.Attribute
            ):
                if dec.func.attrname in REQUIRED_DECORATOR_NAMES:
                    return True

        return False


def register(linter):  # pylint: disable=missing-trace-io
    linter.register_checker(RequireTraceIOChecker(linter))
