# backend/app/core/services/ExecutionService.py
import io
import contextlib
import time
import traceback
from typing import Any, Dict


def run_code_sandboxed(code: str) -> Dict[str, Any]:
    status = "ok"
    stdout = ""
    stderr = ""
    error_type = None

    # 1) bloqueos anti-abuso
    banned = ["import", "__", "open(", "os.", "sys.", "subprocess", "eval(", "exec("]
    if any(b in code for b in banned):
        return {
            "status": "error",
            "stdout": "",
            "stderr": "Operation not allowed by sandbox",
            "error_type": "SandboxError",
            "runtime_ms": None,
        }

    # 2) builtins permitidos
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
    }
    g = {"__builtins__": allowed_builtins}
    l: Dict[str, Any] = {}

    buf_out, buf_err = io.StringIO(), io.StringIO()

    try:
        code_obj = compile(code, "<student>", "exec")
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            exec(code_obj, g, l)
        status = "ok"
    except Exception as e:
        status = "error"
        error_type = e.__class__.__name__
        traceback.print_exc(file=buf_err)
    finally:
        stdout = buf_out.getvalue()
        stderr = buf_err.getvalue()

    return {
        "status": status,
        "stdout": stdout,
        "stderr": stderr,
        "error_type": error_type,
        "runtime_ms": None,
    }
