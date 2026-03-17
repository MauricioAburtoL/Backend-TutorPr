# backend/app/core/services/ExecutionService.py
import ast
import io
import contextlib
import time
import traceback
import builtins
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Configuración del sandbox
# ---------------------------------------------------------------------------

# Módulos seguros para ejercicios de aula
_ALLOWED_MODULES = {"random", "math", "statistics", "decimal", "fractions"}

# Atributos dunder que permiten escalar privilegios fuera del sandbox.
# NOTA: __init__, __str__, __repr__, __len__, etc. NO están aquí → son permitidos.
_DANGEROUS_ATTRS = {
    "__class__", "__bases__", "__mro__", "__subclasses__",
    "__globals__", "__locals__", "__code__", "__builtins__",
    "__import__", "__reduce__", "__reduce_ex__",
}

# Llamadas a funciones built-in peligrosas
_DANGEROUS_CALLS = {"eval", "exec", "open", "compile", "__import__"}


def _ast_check(code: str) -> str | None:
    """
    Analiza el AST del código para detectar patrones peligrosos.
    Retorna un mensaje de error descriptivo o None si el código es seguro.
    Usa el árbol sintáctico en lugar de comparación de substrings, por lo que
    puede distinguir __init__ (seguro) de __class__ (peligroso).
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None  # El error de sintaxis lo maneja exec() más adelante

    for node in ast.walk(tree):

        # -- Imports: solo permitir módulos de la whitelist --
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split(".")[0]
                if module not in _ALLOWED_MODULES:
                    return f"Módulo no permitido: '{module}'"

        elif isinstance(node, ast.ImportFrom):
            module = (node.module or "").split(".")[0]
            if module not in _ALLOWED_MODULES:
                return f"Módulo no permitido: '{module}'"

        # -- Acceso a atributos peligrosos (.e.g __class__, __mro__) --
        elif isinstance(node, ast.Attribute):
            if node.attr in _DANGEROUS_ATTRS:
                return f"Acceso no permitido: '{node.attr}'"

        # -- Llamadas directas a funciones peligrosas --
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in _DANGEROUS_CALLS:
                return f"Función no permitida: '{node.func.id}'"

    return None


def _make_restricted_import(allowed: set):
    """
    Crea un __import__ restringido que solo permite importar módulos de la whitelist.
    Se inyecta en los builtins del exec para que 'import random' funcione
    pero 'import os' falle en tiempo de ejecución (doble protección tras el AST check).
    """
    _real_import = builtins.__import__

    def _restricted_import(name, *args, **kwargs):
        base = name.split(".")[0]
        if base not in allowed:
            raise ImportError(f"Módulo no permitido: '{name}'")
        return _real_import(name, *args, **kwargs)

    return _restricted_import


# ---------------------------------------------------------------------------
# Sandbox principal
# ---------------------------------------------------------------------------

def run_code_sandboxed(code: str) -> Dict[str, Any]:
    """
    Ejecuta el código del estudiante en un entorno controlado (sandbox).
    1. Valida el AST para detectar patrones peligrosos (imports, attrs, calls).
    2. Ejecuta con builtins restringidos y __import__ personalizado.
    """

    # 1) Análisis estático del AST
    error_msg = _ast_check(code)
    if error_msg:
        return {
            "status": "error",
            "stdout": "",
            "stderr": error_msg,
            "error_type": "SandboxError",
            "runtime_ms": None,
        }

    # 2) Builtins permitidos para ejercicios de programación
    allowed_builtins = {
        # I/O
        "print": print,
        "input": input,
        # Secuencias y colecciones
        "range": range,
        "len": len,
        "enumerate": enumerate,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        # Tipos
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        # Matemáticas básicas
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
        "round": round,
        "pow": pow,
        "divmod": divmod,
        # Utilidades
        "sorted": sorted,
        "reversed": reversed,
        "zip": zip,
        "map": map,
        "filter": filter,
        "isinstance": isinstance,
        "issubclass": issubclass,
        "type": type,
        # Excepciones comunes
        "Exception": Exception,
        "ValueError": ValueError,
        "TypeError": TypeError,
        "IndexError": IndexError,
        "KeyError": KeyError,
        "ZeroDivisionError": ZeroDivisionError,
        "NameError": NameError,
        "StopIteration": StopIteration,
        # Import restringido (doble protección)
        "__import__": _make_restricted_import(_ALLOWED_MODULES),
        # Necesario para que las clases funcionen correctamente
        "__build_class__": __build_class__,
        "__name__": "__main__",
    }

    g = {"__builtins__": allowed_builtins}
    l: Dict[str, Any] = {}
    buf_out, buf_err = io.StringIO(), io.StringIO()
    status = "ok"
    stdout = ""
    stderr = ""
    error_type = None
    runtime_ms = None

    try:
        start_time = time.perf_counter()
        code_obj = compile(code, "<student>", "exec")
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            exec(code_obj, g, l)
        status = "ok"
        runtime_ms = (time.perf_counter() - start_time) * 1000
    except Exception as e:
        status = "error"
        error_type = e.__class__.__name__
        traceback.print_exc(file=buf_err)
        runtime_ms = None
    finally:
        stdout = buf_out.getvalue()
        stderr = buf_err.getvalue()

    return {
        "status": status,
        "stdout": stdout,
        "stderr": stderr,
        "error_type": error_type,
        "runtime_ms": runtime_ms,
    }


# ---------------------------------------------------------------------------
# Validación pedagógica
# ---------------------------------------------------------------------------

def validate_logic(actual_output: str, test_cases: List[Any]) -> Dict[str, Any]:
    """
    Compara la salida obtenida del sandbox contra los casos de prueba definidos.
    Aplica normalización de espacios y saltos de línea.
    """
    if not test_cases:
        return {"is_correct": True, "failed_case": None}

    for case in test_cases:
        clean_actual = actual_output.strip()
        clean_expected = case.expected_output.strip()

        if clean_actual != clean_expected:
            return {
                "is_correct": False,
                "failed_case": clean_expected if not case.is_hidden else "Oculto"
            }

    return {"is_correct": True, "failed_case": None}
