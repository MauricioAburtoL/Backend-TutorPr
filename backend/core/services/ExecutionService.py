# backend/app/core/services/ExecutionService.py
import io
import contextlib
import time
import traceback
from typing import Any, Dict, List

def run_code_sandboxed(code: str) -> Dict[str, Any]:
    """
    Ejecuta el código del estudiante en un entorno controlado (sandbox)
    para capturar stdout, stderr y posibles errores.
    """
    status = "ok"
    stdout = ""
    stderr = ""
    error_type = None

    # 1) Bloqueos anti-abuso (Seguridad básica)
    banned = ["import", "__", "open(", "os.", "sys.", "subprocess", "eval(", "exec("]
    if any(b in code for b in banned):
        return {
            "status": "error",
            "stdout": "",
            "stderr": "Operación no permitida por el sandbox",
            "error_type": "SandboxError",
            "runtime_ms": None,
        }

    # 2) Builtins permitidos para el aprendizaje de programación
    allowed_builtins = {
        "print": print,
        "range": range,
        "len": len,
        "enumerate": enumerate,
        "list": list,
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
        "input": input, # Se añade para futuros ejercicios con entrada
        
        # Excepciones comunes para manejo de errores en el código del alumno
        "Exception": Exception,
        "ValueError": ValueError,
        "TypeError": TypeError,
        "IndexError": IndexError,
        "KeyError": KeyError,
        "ZeroDivisionError": ZeroDivisionError,
        "NameError": NameError,
    }
    
    g = {"__builtins__": allowed_builtins}
    l: Dict[str, Any] = {}
    buf_out, buf_err = io.StringIO(), io.StringIO()

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

def validate_logic(actual_output: str, test_cases: List[Any]) -> Dict[str, Any]:
    """
    Compara la salida obtenida del sandbox contra los casos de prueba definidos.
    Aplica una heurística de robustez limpiando espacios y saltos de línea.
    """
    if not test_cases:
        return {"is_correct": True, "failed_case": None}

    for case in test_cases:
        # Limpieza de strings para permitir flexibilidad al usuario (Heurística de Nielsen #2)
        # Se eliminan espacios en blanco al inicio/final y se normalizan saltos de línea
        clean_actual = actual_output.strip()
        clean_expected = case.expected_output.strip()
        
        # Validación: Si no coinciden, el ejercicio no se marca como completado
        if clean_actual != clean_expected:
            return {
                "is_correct": False, 
                "failed_case": clean_expected if not case.is_hidden else "Oculto"
            }
                
    return {"is_correct": True, "failed_case": None}