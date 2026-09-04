"""Intérprete cerrado para árboles declarativos; nunca utiliza eval()."""

from __future__ import annotations

import math
import operator
from typing import Any, Callable, Dict


class OracleConfigurationError(ValueError):
    """El árbol del oráculo contiene una forma u operación no autorizada."""


_BINARY: Dict[str, Callable[[Any, Any], Any]] = {
    "add": operator.add,
    "subtract": operator.sub,
    "multiply": operator.mul,
    "divide": operator.truediv,
    "floor_divide": operator.floordiv,
    "modulo": operator.mod,
    "power": operator.pow,
    "equals": operator.eq,
    "not_equals": operator.ne,
    "less_than": operator.lt,
    "less_or_equal": operator.le,
    "greater_than": operator.gt,
    "greater_or_equal": operator.ge,
}


def _bounded(value: Any) -> Any:
    if isinstance(value, str) and len(value) > 10_000:
        raise OracleConfigurationError("El oráculo produjo una cadena demasiado grande")
    if isinstance(value, (list, tuple, dict, set)) and len(value) > 1_000:
        raise OracleConfigurationError("El oráculo produjo una colección demasiado grande")
    if isinstance(value, float) and not math.isfinite(value):
        raise OracleConfigurationError("El oráculo produjo un número no finito")
    return value


def evaluate_expression(
    node: Dict[str, Any],
    inputs: Dict[str, Any],
    *,
    depth: int = 0,
    budget: list[int] | None = None,
) -> Any:
    """Evalúa un árbol JSON mediante una lista cerrada de operaciones."""
    if budget is None:
        budget = [100]
    budget[0] -= 1
    if budget[0] < 0 or depth > 20:
        raise OracleConfigurationError("El árbol del oráculo excede su complejidad máxima")
    if not isinstance(node, dict):
        raise OracleConfigurationError("Cada nodo del oráculo debe ser un objeto")

    node_kinds = [key for key in ("input", "constant", "operation") if key in node]
    if len(node_kinds) != 1:
        raise OracleConfigurationError(
            "Cada nodo debe declarar exactamente input, constant u operation"
        )

    if "input" in node:
        input_id = node["input"]
        if input_id not in inputs:
            raise OracleConfigurationError(f"Entrada no definida: {input_id}")
        return _bounded(inputs[input_id])

    if "constant" in node:
        return _bounded(node["constant"])

    operation = node["operation"]
    raw_arguments = node.get("arguments", [])
    if not isinstance(raw_arguments, list):
        raise OracleConfigurationError("arguments debe ser una lista")
    arguments = [
        evaluate_expression(arg, inputs, depth=depth + 1, budget=budget)
        for arg in raw_arguments
    ]

    if operation in _BINARY:
        if len(arguments) != 2:
            raise OracleConfigurationError(f"{operation} requiere dos argumentos")
        return _bounded(_BINARY[operation](arguments[0], arguments[1]))

    if operation == "negate" and len(arguments) == 1:
        return _bounded(-arguments[0])
    if operation == "absolute" and len(arguments) == 1:
        return _bounded(abs(arguments[0]))
    if operation == "length" and len(arguments) == 1:
        return len(arguments[0])
    if operation == "reverse" and len(arguments) == 1:
        return _bounded(arguments[0][::-1])
    if operation == "normalize" and len(arguments) == 1:
        return "".join(str(arguments[0]).lower().split())
    if operation == "sum" and len(arguments) == 1:
        return _bounded(sum(arguments[0]))
    if operation == "minimum" and arguments:
        values = arguments[0] if len(arguments) == 1 else arguments
        return _bounded(min(values))
    if operation == "maximum" and arguments:
        values = arguments[0] if len(arguments) == 1 else arguments
        return _bounded(max(values))
    if operation == "sort" and len(arguments) == 1:
        return _bounded(sorted(arguments[0]))
    if operation == "all" and len(arguments) == 1:
        return all(arguments[0])
    if operation == "any" and len(arguments) == 1:
        return any(arguments[0])

    raise OracleConfigurationError(f"Operación no autorizada: {operation}")
