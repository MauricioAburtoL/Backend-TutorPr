# backend/app/core/services/ExecutionService.py
import ast
import io
import contextlib
import json
from pathlib import Path
import subprocess
import sys
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

_EXECUTION_TIMEOUT_SECONDS = 3.0
_MAX_CODE_BYTES = 50_000
_MAX_OUTPUT_CHARS = 100_000


class OutputLimitExceeded(Exception):
    """Interrumpe programas que generan una salida excesiva."""


class InputLimitExceeded(Exception):
    """Interrumpe programas que solicitan más datos de los autorizados."""


class _LimitedStringIO(io.StringIO):
    def __init__(self, limit: int):
        super().__init__()
        self._limit = limit
        self._size = 0

    def write(self, value: str) -> int:
        remaining = self._limit - self._size
        if remaining <= 0:
            raise OutputLimitExceeded(
                f"La salida superó el límite de {self._limit} caracteres"
            )

        if len(value) > remaining:
            super().write(value[:remaining])
            self._size += remaining
            raise OutputLimitExceeded(
                f"La salida superó el límite de {self._limit} caracteres"
            )

        written = super().write(value)
        self._size += written
        return written


def compose_test_code(code: str, test_code: str | None = None) -> str:
    """Compone la solución con una comprobación interna opcional."""
    private_check = (test_code or "").strip()
    if not private_check:
        return code
    return f"{code.rstrip()}\n\n{private_check}\n"


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

def _run_code_in_process(
    code: str,
    input_data: str | None = None,
    max_output_chars: int | None = None,
    max_input_requests: int | None = None,
) -> Dict[str, Any]:
    """
    Ejecuta código restringido dentro del proceso trabajador desechable.
    1. Valida el AST para detectar patrones peligrosos (imports, attrs, calls).
    2. Ejecuta con builtins restringidos y __import__ personalizado.

    Los límites de salida y de lecturas provienen del contrato del ejercicio
    (`FR-RUN-002`); cuando no se indican se aplican los valores globales.
    """
    output_limit = min(max_output_chars or _MAX_OUTPUT_CHARS, _MAX_OUTPUT_CHARS)
    input_limit = max_input_requests

    # 1) Análisis estático del AST
    error_msg = _ast_check(code)
    if error_msg:
        return {
            "status": "error",
            "stdout": "",
            "stderr": error_msg,
            "error_type": "SandboxError",
            "runtime_ms": None,
            "events": [],
        }

    execution_events: List[Dict[str, Any]] = []

    def record_event(event: str, **payload: Any) -> None:
        execution_events.append({
            "event": event,
            "sequence": len(execution_events) + 1,
            **payload,
        })

    # Entrada aislada para este caso de prueba. Imita input(): consume una
    # línea, elimina el salto final y lanza EOFError cuando ya no hay datos.
    input_stream = io.StringIO(input_data or "")
    input_requests = 0

    def sandbox_input(prompt: str = "") -> str:
        nonlocal input_requests
        input_requests += 1
        if input_limit is not None and input_requests > input_limit:
            raise InputLimitExceeded(
                f"El programa solicitó más de {input_limit} datos de entrada"
            )
        if prompt:
            record_event("input_prompt", text=str(prompt))
            builtins.print(prompt, end="")
        line = input_stream.readline()
        if line == "":
            raise EOFError("No hay más datos de entrada para este caso de prueba")
        value = line.rstrip("\r\n")
        record_event("input_value", value=value)
        return value

    def sandbox_print(
        *values: Any,
        sep: str | None = " ",
        end: str | None = "\n",
        file=None,
        flush: bool = False,
    ) -> None:
        effective_sep = " " if sep is None else sep
        effective_end = "\n" if end is None else end
        if file is None or file is sys.stdout:
            rendered = effective_sep.join(str(value) for value in values) + effective_end
            record_event("print", text=rendered)
        builtins.print(
            *values,
            sep=sep,
            end=end,
            file=file,
            flush=flush,
        )

    def sandbox_capture(value: Any) -> None:
        """Registra el retorno solicitado por el arnés sin imprimirlo en consola."""
        record_event("evaluation_result", value_repr=repr(value))

    # 2) Builtins permitidos para ejercicios de programación
    allowed_builtins = {
        # I/O
        "print": sandbox_print,
        "input": sandbox_input,
        "__tutorats_capture__": sandbox_capture,
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
    buf_out = _LimitedStringIO(output_limit)
    buf_err = _LimitedStringIO(output_limit)
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
        record_event("exception", error_type=error_type)
        try:
            traceback.print_exc(file=buf_err)
        except OutputLimitExceeded:
            pass
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
        "events": execution_events,
    }


def run_code_sandboxed(
    code: str,
    input_data: str | None = None,
    timeout_seconds: float = _EXECUTION_TIMEOUT_SECONDS,
    max_output_chars: int | None = None,
    max_input_requests: int | None = None,
) -> Dict[str, Any]:
    """
    Ejecuta cada solución en un subproceso desechable.

    El proceso principal nunca ejecuta el código del estudiante directamente y
    termina al trabajador si rebasa el tiempo máximo, incluso cuando hay un
    ciclo infinito.
    """
    if len(code.encode("utf-8")) > _MAX_CODE_BYTES:
        return {
            "status": "error",
            "stdout": "",
            "stderr": f"El código supera el límite de {_MAX_CODE_BYTES} bytes",
            "error_type": "SandboxError",
            "runtime_ms": None,
            "events": [],
        }

    error_msg = _ast_check(code)
    if error_msg:
        return {
            "status": "error",
            "stdout": "",
            "stderr": error_msg,
            "error_type": "SandboxError",
            "runtime_ms": None,
            "events": [],
        }

    payload = json.dumps({
        "code": code,
        "input_data": input_data,
        "max_output_chars": max_output_chars,
        "max_input_requests": max_input_requests,
    })
    project_root = Path(__file__).resolve().parents[3]

    try:
        completed = subprocess.run(
            [sys.executable, "-m", "backend.core.services.execution_worker"],
            input=payload,
            text=True,
            capture_output=True,
            cwd=str(project_root),
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "stdout": "",
            "stderr": (
                "La ejecución superó el tiempo máximo de "
                f"{timeout_seconds:g} segundos"
            ),
            "error_type": "TimeoutError",
            "runtime_ms": timeout_seconds * 1000,
            "events": [{"event": "timeout", "sequence": 1}],
        }
    except OSError:
        return {
            "status": "error",
            "stdout": "",
            "stderr": "No se pudo iniciar el entorno aislado de ejecución",
            "error_type": "WorkerError",
            "runtime_ms": None,
            "events": [],
        }

    if completed.returncode != 0:
        return {
            "status": "error",
            "stdout": "",
            "stderr": "El entorno aislado terminó de forma inesperada",
            "error_type": "WorkerError",
            "runtime_ms": None,
            "events": [],
        }

    try:
        result = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError):
        return {
            "status": "error",
            "stdout": "",
            "stderr": "El entorno aislado devolvió una respuesta inválida",
            "error_type": "WorkerError",
            "runtime_ms": None,
            "events": [],
        }

    if not isinstance(result, dict):
        return {
            "status": "error",
            "stdout": "",
            "stderr": "El entorno aislado devolvió una respuesta inválida",
            "error_type": "WorkerError",
            "runtime_ms": None,
            "events": [],
        }

    return result
