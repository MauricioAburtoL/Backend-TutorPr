"""Detección e instrumentación temporal de entradas del código del estudiante."""

from __future__ import annotations

import ast
import copy
import itertools
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

from .contracts import InputSlot


@dataclass(frozen=True)
class LiteralCandidate:
    lineno: int
    col_offset: int
    target: str
    value: Any
    element_index: int | None = None

    @property
    def key(self) -> str:
        suffix = "" if self.element_index is None else f"[{self.element_index}]"
        return f"{self.lineno}:{self.col_offset}:{self.target}{suffix}"


def count_input_calls(code: str) -> int:
    tree = ast.parse(code)
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "input"
    )


def _literal_value(node: ast.AST) -> tuple[bool, Any]:
    if isinstance(node, ast.Constant):
        return True, node.value
    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, (ast.USub, ast.UAdd))
        and isinstance(node.operand, ast.Constant)
        and isinstance(node.operand.value, (int, float))
    ):
        value = node.operand.value
        return True, -value if isinstance(node.op, ast.USub) else value
    if isinstance(node, (ast.List, ast.Tuple)):
        values = []
        for element in node.elts:
            valid, value = _literal_value(element)
            if not valid:
                return False, None
            values.append(value)
        return True, values
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"int", "float", "str", "bool"}
        and len(node.args) == 1
        and not node.keywords
    ):
        valid, value = _literal_value(node.args[0])
        if not valid:
            return False, None
        try:
            return True, {"int": int, "float": float, "str": str, "bool": bool}[
                node.func.id
            ](value)
        except (TypeError, ValueError):
            return False, None
    return False, None


def _names_in(node: ast.AST) -> set[str]:
    return {
        child.id
        for child in ast.walk(node)
        if isinstance(child, ast.Name)
    }


def observable_variables(code: str) -> set[str]:
    """Variables cuyo valor alcanza una salida observable (`FR-BIND-009`).

    Construye el grafo de dependencias entre asignaciones y lo recorre hacia
    atrás desde lo que el programa imprime o retorna. Sirve para excluir del
    enlace automático los literales que solo participan en mensajes, y con ello
    reducir las combinaciones antes de permutarlas.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return set()

    dependencies: Dict[str, set[str]] = {}
    seeds: set[str] = set()

    def depend(target: str, node: ast.AST) -> None:
        dependencies.setdefault(target, set()).update(_names_in(node))

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                for name in _names_in(target):
                    depend(name, node.value)
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            if node.value is not None:
                for name in _names_in(node.target):
                    depend(name, node.value)
        elif isinstance(node, ast.For):
            for name in _names_in(node.target):
                depend(name, node.iter)
        elif isinstance(node, ast.Return) and node.value is not None:
            seeds.update(_names_in(node.value))
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "print":
                for argument in [*node.args, *(kw.value for kw in node.keywords)]:
                    seeds.update(_names_in(argument))
            elif isinstance(node.func, ast.Attribute) and isinstance(
                node.func.value, ast.Name
            ):
                # `numeros.append(x)` hace que la colección dependa de `x`.
                for argument in node.args:
                    depend(node.func.value.id, argument)

    reachable = set(seeds)
    pending = list(seeds)
    while pending:
        current = pending.pop()
        for name in dependencies.get(current, ()):
            if name not in reachable:
                reachable.add(name)
                pending.append(name)
    return reachable


def find_literal_candidates(
    code: str,
    *,
    restrict_to: set[str] | None = None,
) -> List[LiteralCandidate]:
    tree = ast.parse(code)
    candidates: List[LiteralCandidate] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                valid, value = _literal_value(node.value)
                if valid:
                    candidates.append(
                        LiteralCandidate(
                            lineno=node.lineno,
                            col_offset=node.col_offset,
                            target=target.id,
                            value=value,
                        )
                    )
            elif (
                isinstance(target, (ast.Tuple, ast.List))
                and isinstance(node.value, (ast.Tuple, ast.List))
                and len(target.elts) == len(node.value.elts)
            ):
                for index, (target_item, value_item) in enumerate(
                    zip(target.elts, node.value.elts)
                ):
                    if not isinstance(target_item, ast.Name):
                        continue
                    valid, value = _literal_value(value_item)
                    if valid:
                        candidates.append(
                            LiteralCandidate(
                                lineno=node.lineno,
                                col_offset=node.col_offset,
                                target=target_item.id,
                                value=value,
                                element_index=index,
                            )
                        )
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is None:
                continue
            valid, value = _literal_value(node.value)
            if valid:
                candidates.append(
                    LiteralCandidate(
                        lineno=node.lineno,
                        col_offset=node.col_offset,
                        target=node.target.id,
                        value=value,
                    )
                )
    if restrict_to is not None:
        filtered = [item for item in candidates if item.target in restrict_to]
        # Si el análisis no alcanza ningún literal, se conserva el conjunto
        # completo: la reducción es una optimización, no un criterio de rechazo.
        if filtered:
            candidates = filtered
    return sorted(candidates, key=lambda item: (item.lineno, item.col_offset))


def resolve_function_target(
    code: str,
    preferred_name: str | None,
    parameter_count: int | None,
) -> tuple[str | None, str | None]:
    """Localiza la función objetivo sin exigir el nombre sugerido (`FR-FUN-001`).

    Devuelve el nombre encontrado, o la causa por la que no fue posible.
    """
    tree = ast.parse(code)
    definitions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    if not definitions:
        return None, "no_function_defined"

    if preferred_name and preferred_name in {node.name for node in definitions}:
        return preferred_name, None

    if parameter_count is None:
        if len(definitions) == 1:
            return definitions[0].name, None
        return None, "ambiguous_function_target"

    compatible = [
        node
        for node in definitions
        if len(node.args.posonlyargs) + len(node.args.args) == parameter_count
        and node.args.vararg is None
    ]
    if len(compatible) == 1:
        return compatible[0].name, None
    if not compatible:
        return None, "no_compatible_function"
    return None, "ambiguous_function_target"


def _matches_slot(value: Any, slot: InputSlot) -> bool:
    if slot.value_type == "integer":
        return type(value) is int
    if slot.value_type == "number":
        return type(value) in {int, float}
    if slot.value_type == "string":
        return isinstance(value, str)
    if slot.value_type == "boolean":
        return type(value) is bool
    if slot.value_type in {"array", "tuple", "matrix"}:
        return isinstance(value, (list, tuple))
    return False


def candidate_mappings(
    slots: Sequence[InputSlot],
    candidates: Sequence[LiteralCandidate],
    *,
    maximum: int,
) -> List[Dict[str, LiteralCandidate]]:
    mappings: List[Dict[str, LiteralCandidate]] = []
    for ordered in itertools.permutations(candidates, len(slots)):
        if not all(_matches_slot(candidate.value, slot) for slot, candidate in zip(slots, ordered)):
            continue
        mappings.append({slot.id: candidate for slot, candidate in zip(slots, ordered)})
        if len(mappings) > maximum:
            return []
    return mappings


def _value_node(value: Any) -> ast.AST:
    return ast.parse(repr(value), mode="eval").body


class _LiteralReplacement(ast.NodeTransformer):
    def __init__(
        self,
        replacements: Dict[str, tuple[LiteralCandidate, Any]],
    ) -> None:
        self.replacements = replacements

    def _for_node(self, node: ast.AST) -> List[tuple[LiteralCandidate, Any]]:
        return [
            item
            for item in self.replacements.values()
            if item[0].lineno == getattr(node, "lineno", None)
            and item[0].col_offset == getattr(node, "col_offset", None)
        ]

    def visit_Assign(self, node: ast.Assign):
        self.generic_visit(node)
        matches = self._for_node(node)
        for candidate, value in matches:
            if candidate.element_index is None:
                node.value = _value_node(value)
            elif isinstance(node.value, (ast.Tuple, ast.List)):
                node.value.elts[candidate.element_index] = _value_node(value)
        return node

    def visit_AnnAssign(self, node: ast.AnnAssign):
        self.generic_visit(node)
        matches = self._for_node(node)
        if matches:
            node.value = _value_node(matches[0][1])
        return node


def code_for_literal_case(
    code: str,
    mapping: Dict[str, LiteralCandidate],
    inputs: Dict[str, Any],
) -> str:
    tree = ast.parse(code)
    replacements = {
        slot_id: (candidate, inputs[slot_id])
        for slot_id, candidate in mapping.items()
    }
    transformed = _LiteralReplacement(replacements).visit(copy.deepcopy(tree))
    ast.fix_missing_locations(transformed)
    return ast.unparse(transformed)


def serialize_stdin(
    slots: Sequence[InputSlot],
    inputs: Dict[str, Any],
    layout: str,
) -> str:
    values = [inputs[slot.id] for slot in slots]

    def scalar(value: Any) -> str:
        if isinstance(value, bool):
            return "True" if value else "False"
        return str(value)

    if layout == "single_line_tokens":
        flattened: List[Any] = []
        for value in values:
            if isinstance(value, (list, tuple)):
                flattened.extend(value)
            else:
                flattened.append(value)
        return " ".join(scalar(value) for value in flattened) + "\n"

    if layout == "count_then_values":
        if len(values) != 1 or not isinstance(values[0], (list, tuple)):
            raise ValueError("count_then_values requiere una sola colección")
        collection = values[0]
        return "\n".join([str(len(collection)), *(scalar(v) for v in collection)]) + "\n"

    lines: List[str] = []
    for value in values:
        if isinstance(value, (list, tuple)):
            lines.extend(scalar(item) for item in value)
        else:
            lines.append(scalar(value))
    if layout == "values_then_blank":
        # Los ciclos con centinela leen hasta recibir una entrada vacía.
        lines.append("")
    return "\n".join(lines) + "\n"


def stdin_value_count(slots: Sequence[InputSlot], inputs: Dict[str, Any], layout: str) -> int:
    """Cantidad de datos que el programa debería consumir con ese formato."""
    if layout == "single_line_tokens":
        return 1
    total = 0
    for slot in slots:
        value = inputs[slot.id]
        total += len(value) if isinstance(value, (list, tuple)) else 1
    if layout == "count_then_values":
        total += 1
    return total

