"""Extracción tipada de resultados a partir de eventos de ejecución."""

from __future__ import annotations

import ast
import math
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from .contracts import OutputObservation


_NUMBER = re.compile(
    r"(?<![\w.])[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?(?![\w.])"
)
_WORDS = re.compile(r"[^\W\d_]+", flags=re.UNICODE)
_TOKEN_SEPARATOR = re.compile(r"[\s,;]+")

_TRUE_WORDS = {"true", "verdadero", "si", "cierto", "afirmativo"}
_FALSE_WORDS = {"false", "falso", "no", "incorrecto", "negativo"}
_NEGATION_WORDS = {"no", "nunca", "tampoco", "ningun", "ninguna", "sin", "jamas"}


@dataclass(frozen=True)
class ParsedOutput:
    status: str
    value: Any = None
    candidates: int = 0
    values: Tuple[Any, ...] = field(default_factory=tuple)


def _fold(text: str) -> str:
    """Normaliza acentos y mayúsculas para comparar vocabulario declarado."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _parse_boolean(text: str, observation: OutputObservation) -> tuple[bool, Any]:
    words = _WORDS.findall(_fold(text))
    if not words:
        return False, None

    for word in reversed(words):
        if word in _TRUE_WORDS:
            return True, True
        if word in _FALSE_WORDS:
            return True, False

    if observation.boolean_profile != "negation_aware":
        return False, None

    # Perfil declarado (`FR-OUT-008`): una frase que menciona el concepto del
    # ejercicio afirma, salvo que incluya una negación explícita. Sin palabras
    # declaradas no se interpreta nada, para no volver permisivo el motor.
    keywords = {_fold(word) for word in observation.boolean_keywords}
    if not keywords or not keywords.intersection(words):
        return False, None
    return True, not any(word in _NEGATION_WORDS for word in words)


def _parse_scalar_token(token: str, item_type: str | None) -> tuple[bool, Any]:
    token = token.strip()
    if not token:
        return False, None
    if item_type == "string":
        return True, token
    try:
        return True, int(token)
    except ValueError:
        pass
    try:
        value = float(token)
    except ValueError:
        return False, None
    if item_type == "integer":
        return False, None
    return True, value


def _as_collection(value: Any, value_type: str) -> tuple[bool, Any]:
    if value_type == "array" and isinstance(value, (list, tuple)):
        return True, list(value)
    if value_type == "tuple" and isinstance(value, (list, tuple)):
        return True, tuple(value)
    if (
        value_type == "matrix"
        and isinstance(value, (list, tuple))
        and all(isinstance(row, (list, tuple)) for row in value)
    ):
        return True, [list(row) for row in value]
    return False, None


def _parse_literal_collection(text: str, value_type: str) -> tuple[bool, Any]:
    cleaned = text.strip()
    fragments = [cleaned]
    fragments.extend(re.findall(r"\[[^\n]*\]|\([^\n]*\)", cleaned))
    for fragment in reversed(fragments):
        try:
            value = ast.literal_eval(fragment)
        except (SyntaxError, ValueError):
            continue
        parsed, result = _as_collection(value, value_type)
        if parsed:
            return True, result
    return False, None


def _parse_joined_line(text: str, observation: OutputObservation) -> tuple[bool, Any]:
    """Reconoce `print(" ".join(...))` y formas equivalentes."""
    tokens = [token for token in _TOKEN_SEPARATOR.split(text.strip()) if token]
    if len(tokens) < 2:
        return False, None
    values: List[Any] = []
    for token in tokens:
        parsed, value = _parse_scalar_token(token, observation.item_type)
        if not parsed:
            return False, None
        values.append(value)
    return _as_collection(values, observation.value_type)


def _parse_text(text: str, observation: OutputObservation) -> tuple[bool, Any]:
    value_type = observation.value_type
    cleaned = text.strip()

    if value_type == "string":
        return (bool(cleaned), cleaned)

    if value_type in {"number", "integer"}:
        matches = _NUMBER.findall(cleaned)
        if not matches:
            return False, None
        token = matches[-1]
        try:
            value = float(token) if value_type == "number" else int(token)
        except ValueError:
            return False, None
        return True, value

    if value_type == "boolean":
        return _parse_boolean(cleaned, observation)

    if value_type in {"array", "tuple", "matrix"}:
        formats = observation.collection_formats
        if "literal" in formats:
            parsed, value = _parse_literal_collection(cleaned, value_type)
            if parsed:
                return True, value
        if "joined_line" in formats:
            parsed, value = _parse_joined_line(cleaned, observation)
            if parsed:
                return True, value

    return False, None


def _per_line_candidate(
    texts: Sequence[str],
    observation: OutputObservation,
) -> tuple[bool, Any]:
    """Agrupa la serie final de impresiones de un solo elemento en una colección.

    Cubre la forma más frecuente del temario de listas: recorrer la colección e
    imprimir un elemento por línea (`FR-OUT-007`).
    """
    values: List[Any] = []
    for text in reversed(texts):
        tokens = [token for token in _TOKEN_SEPARATOR.split(text.strip()) if token]
        if len(tokens) != 1:
            break
        parsed, value = _parse_scalar_token(tokens[0], observation.item_type)
        if not parsed:
            break
        values.append(value)
    if len(values) < 2:
        return False, None
    values.reverse()
    return _as_collection(values, observation.value_type)


def _print_texts(events: Iterable[Dict[str, Any]]) -> List[str]:
    return [
        str(event.get("text", ""))
        for event in events
        if event.get("event") == "print"
    ]


def _resolve(candidates: List[Any], observation: OutputObservation) -> ParsedOutput:
    if not candidates:
        return ParsedOutput(status="output_inconclusive")
    if observation.selection == "unique_parseable" and len(candidates) != 1:
        return ParsedOutput(
            status="output_inconclusive",
            candidates=len(candidates),
            values=tuple(candidates),
        )
    return ParsedOutput(
        status="parsed",
        value=candidates[-1],
        candidates=len(candidates),
        values=tuple(candidates),
    )


def extract_output(
    events: Iterable[Dict[str, Any]],
    observation: OutputObservation,
) -> ParsedOutput:
    texts = _print_texts(events)
    candidates: List[Any] = []
    for text in texts:
        parsed, value = _parse_text(text, observation)
        if parsed:
            candidates.append(value)

    if (
        observation.value_type in {"array", "tuple", "matrix"}
        and "per_line" in observation.collection_formats
    ):
        parsed, value = _per_line_candidate(texts, observation)
        if parsed:
            candidates.append(value)

    return _resolve(candidates, observation)


def _parse_repr(text: str, observation: OutputObservation) -> tuple[bool, Any]:
    value_type = observation.value_type
    try:
        value = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return _parse_text(text, observation)

    if value_type == "integer" and type(value) is int:
        return True, value
    if value_type == "number" and type(value) in {int, float}:
        return True, value
    if value_type == "string" and isinstance(value, str):
        return True, value
    if value_type == "boolean" and type(value) is bool:
        return True, value
    return _as_collection(value, value_type)


def extract_captured_output(
    events: Iterable[Dict[str, Any]],
    observation: OutputObservation,
) -> ParsedOutput:
    """Extrae el retorno capturado por el arnés de funciones."""
    candidates: List[Any] = []
    for event in events:
        if event.get("event") != "evaluation_result":
            continue
        parsed, value = _parse_repr(str(event.get("value_repr", "")), observation)
        if parsed:
            candidates.append(value)
    return _resolve(candidates, observation)


def values_match(actual: Any, expected: Any, observation: OutputObservation) -> bool:
    if observation.value_type == "number":
        try:
            return math.isclose(
                float(actual),
                float(expected),
                rel_tol=observation.relative_tolerance,
                abs_tol=observation.absolute_tolerance,
            )
        except (TypeError, ValueError):
            return False
    if observation.value_type == "integer":
        return type(actual) is int and type(expected) is int and actual == expected
    if observation.value_type == "boolean":
        return type(actual) is bool and type(expected) is bool and actual == expected
    if observation.value_type in {"array", "tuple"}:
        return (
            isinstance(actual, (list, tuple))
            and isinstance(expected, (list, tuple))
            and list(actual) == list(expected)
        )
    if observation.value_type == "matrix":
        return (
            isinstance(actual, (list, tuple))
            and isinstance(expected, (list, tuple))
            and [list(row) for row in actual] == [list(row) for row in expected]
        )
    return actual == expected


def any_candidate_matches(
    parsed: ParsedOutput,
    expected: Any,
    observation: OutputObservation,
) -> bool:
    """Indica si algún candidato descartado coincidía con el resultado esperado."""
    return any(values_match(value, expected, observation) for value in parsed.values)
