"""Proceso desechable encargado de ejecutar una solución de estudiante."""

import json
import sys

from .ExecutionService import _run_code_in_process


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
        result = _run_code_in_process(
            code=payload.get("code", ""),
            input_data=payload.get("input_data"),
        )
    except Exception as exc:
        result = {
            "status": "error",
            "stdout": "",
            "stderr": f"Error interno del ejecutor: {exc.__class__.__name__}",
            "error_type": "WorkerError",
            "runtime_ms": None,
        }

    sys.stdout.write(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
