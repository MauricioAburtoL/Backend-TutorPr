# backend/adapters/python/detectors_py.py
"""
Analisis estatico de codigo Python usando stdlib (ast + tokenize).
Detecta MULTIPLES errores de sintaxis/indentacion en una sola pasada.
"""
import ast
import io
import tokenize
from typing import List, Dict, Any


def analyze_syntax(code: str) -> List[Dict[str, Any]]:
    """
    Detecta todos los errores de sintaxis/indentacion posibles
    usando tokenize (nivel lexico) + ast.parse iterativo (nivel gramatical).

    Retorna lista de dicts compatibles con DetectedError:
        [{"line": int, "type": "syntax", "desc": str}, ...]
    """
    if not code or not code.strip():
        return []

    token_errors = _tokenize_errors(code)
    ast_errors = _iterative_parse_errors(code)
    return _deduplicate(token_errors + ast_errors)


def _tokenize_errors(code: str) -> List[Dict[str, Any]]:
    """
    Usa tokenize.generate_tokens() para detectar errores lexicos:
    IndentationError, TokenError (parentesis/strings sin cerrar).
    """
    errors = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(code).readline)
        for _ in tokens:
            pass
    except tokenize.TokenError as e:
        msg, (line, _col) = e.args
        errors.append({
            "line": line,
            "type": "syntax",
            "desc": f"TokenError: {msg}",
        })
    except IndentationError as e:
        errors.append({
            "line": e.lineno or 1,
            "type": "syntax",
            "desc": f"IndentationError: {e.msg}",
        })
    except SyntaxError as e:
        errors.append({
            "line": e.lineno or 1,
            "type": "syntax",
            "desc": f"SyntaxError: {e.msg}",
        })
    return errors


def _iterative_parse_errors(code: str, max_iterations: int = 10) -> List[Dict[str, Any]]:
    """
    Llama ast.parse() en bucle. Al encontrar SyntaxError, lo registra,
    neutraliza la linea con 'pass' (manteniendo indentacion), y reintenta.
    max_iterations evita loops infinitos.
    """
    errors = []
    lines = code.split('\n')
    seen_lines = set()

    for _ in range(max_iterations):
        source = '\n'.join(lines)
        try:
            ast.parse(source)
            break
        except SyntaxError as e:
            err_line = e.lineno or 1

            if err_line in seen_lines:
                break
            seen_lines.add(err_line)

            err_name = type(e).__name__
            errors.append({
                "line": err_line,
                "type": "syntax",
                "desc": f"{err_name}: {e.msg}",
            })

            # Neutralizar la linea problematica manteniendo indentacion
            if 1 <= err_line <= len(lines):
                original = lines[err_line - 1]
                indent = len(original) - len(original.lstrip())
                lines[err_line - 1] = ' ' * indent + 'pass  # neutralized'

    return errors


def _deduplicate(errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Elimina duplicados por linea. Prefiere la descripcion mas larga
    (generalmente mas especifica).
    """
    by_line: Dict[int, Dict[str, Any]] = {}
    for err in errors:
        line = err["line"]
        if line not in by_line or len(err["desc"]) > len(by_line[line]["desc"]):
            by_line[line] = err
    return sorted(by_line.values(), key=lambda e: e["line"])
