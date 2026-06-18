"""Safe compilation of user-supplied time-function expressions.

The notebook (``LIF Model.ipynb``) lets a user type a Python expression such as
``"1.5 + math.sin(t / 10)"`` and turns it into ``lambda t: ...`` via
``compile`` + ``eval`` against the namespace ``{t, math, np}``. That is fine for a
trusted local notebook, but the web app exposes the same mechanism over HTTP, so
arbitrary strings from arbitrary clients reach ``eval``.

This module keeps the *exact same evaluation semantics* (per-timestep scalar
``eval`` over ``{t, math, np}``) but adds two hardening layers the notebook lacks:

1. An AST allow-list walked *before* compilation. Anything outside a small set of
   nodes/names (numbers, ``t``, ``math.*``, ``np.*``, arithmetic, comparisons,
   ternaries) is rejected with a human-readable :class:`ExpressionError`.
2. Evaluation with ``{"__builtins__": {}}`` so that even if a name slipped through,
   builtins like ``open``/``__import__`` are unreachable.

This blocks payloads such as ``__import__("os").system(...)`` or ``t.__class__``
while still allowing the rich math the simulation needs.
"""

from __future__ import annotations

import ast
import math
from typing import Callable

import numpy as np

__all__ = ["ExpressionError", "compile_expression"]


class ExpressionError(ValueError):
    """Raised when a user expression is unsafe or syntactically invalid.

    The message is intended to be safe to surface directly to an end user.
    """


# Names that may appear as a bare identifier in an expression.
_ALLOWED_NAMES = frozenset({"t", "math", "np", "pi", "e"})

# Roots whose attributes/calls are allowed (e.g. ``math.sin``, ``np.where``).
_ALLOWED_ATTR_ROOTS = frozenset({"math", "np"})

# AST node types that are permitted anywhere in the tree.
_ALLOWED_NODES = (
    ast.Expression,
    ast.Constant,
    ast.Name,
    ast.Load,
    ast.BinOp,
    ast.UnaryOp,
    ast.BoolOp,
    ast.Compare,
    ast.IfExp,
    ast.Call,
    ast.Attribute,
    # binary operators
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    # unary operators
    ast.UAdd,
    ast.USub,
    # boolean / comparison operators
    ast.And,
    ast.Or,
    ast.Not,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
)


def _validate(tree: ast.AST, expr: str) -> None:
    """Walk ``tree`` and raise :class:`ExpressionError` on anything not allow-listed."""
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ExpressionError(
                f"'{type(node).__name__}' is not allowed in expressions. "
                f"Use numbers, t, math.*, np.* and arithmetic only."
            )

        # Only numeric/boolean constants — reject strings, bytes, etc.
        if isinstance(node, ast.Constant) and not isinstance(
            node.value, (int, float, bool)
        ):
            raise ExpressionError("Only numeric constants are allowed.")

        # Bare names must be on the allow-list.
        if isinstance(node, ast.Name) and node.id not in _ALLOWED_NAMES:
            raise ExpressionError(
                f"Unknown name '{node.id}'. Allowed: t, math, np, pi, e."
            )

        # Attribute access (and therefore method calls) only on math / np.
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("_"):
                raise ExpressionError("Dunder/private attribute access is not allowed.")
            if not (
                isinstance(node.value, ast.Name)
                and node.value.id in _ALLOWED_ATTR_ROOTS
            ):
                raise ExpressionError(
                    "Attribute access is only allowed on 'math' or 'np'."
                )


def compile_expression(expr: str) -> Callable[[float], float]:
    """Compile a time-function string into a safe callable ``f(t)``.

    Parameters
    ----------
    expr:
        A Python expression in terms of ``t`` (time, ms). ``math``, ``np``, ``pi``
        and ``e`` are in scope. Examples: ``"1.5"``, ``"1.5 + math.sin(t/10)"``,
        ``"np.where(t > 100, 3.0, 0.5)"``.

    Returns
    -------
    Callable[[float], float]
        A function that evaluates the expression at a given time ``t``.

    Raises
    ------
    ExpressionError
        If the expression is empty, syntactically invalid, or uses a construct or
        name outside the allow-list.
    """
    if expr is None or not str(expr).strip():
        raise ExpressionError("Expression is empty.")

    expr = str(expr).strip()

    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise ExpressionError(f"Invalid syntax: {exc.msg}.") from exc

    _validate(tree, expr)

    code = compile(tree, "<expression>", "eval")
    # Empty builtins: even if validation were bypassed, no builtins are reachable.
    base_globals = {"__builtins__": {}}
    base_locals = {"math": math, "np": np, "pi": math.pi, "e": math.e}

    def func(t: float) -> float:
        return eval(code, base_globals, {**base_locals, "t": t})  # noqa: S307

    # Smoke-evaluate once so obvious runtime errors (e.g. domain errors) surface at
    # compile time rather than mid-simulation. A failure here is reported to the user.
    try:
        func(0.0)
    except ExpressionError:
        raise
    except Exception as exc:  # noqa: BLE001 - surface a friendly message
        raise ExpressionError(f"Expression failed to evaluate: {exc}.") from exc

    return func
