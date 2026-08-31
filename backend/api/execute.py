# backend/app/api/execute.py
import hashlib

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

# Importaciones de la capa de infraestructura y núcleo
from ..infra.db import get_db
from ..infra.storage_sqlite import StorageSQLite
from ..core.models import Event
from ..schemas import ExecuteIn
from ..core.services.ExecutionService import compose_test_code, run_code_sandboxed
from ..core.services.ProgressService import ProgressService

router = APIRouter()


def _normalized_output(value: str) -> str:
    return (value or "").strip()


def _code_for_case(code: str, case) -> str:
    """Añade la comprobación privada del caso sin modificar el código guardado."""
    return compose_test_code(code, getattr(case, "test_code", None))


def _execute_test_cases(code: str, test_cases) -> Dict[str, Any]:
    """Ejecuta el programa una vez por caso sin exponer los datos ocultos."""
    if not test_cases:
        return {
            "result": run_code_sandboxed(code),
            "is_correct": False,
            "failed_case": "Sin casos de prueba configurados",
            "test_results": [],
        }

    executions = []
    for index, case in enumerate(test_cases, start=1):
        case_result = run_code_sandboxed(
            _code_for_case(code, case),
            input_data=case.input_data,
        )
        passed = (
            case_result["status"] == "ok"
            and _normalized_output(case_result["stdout"])
            == _normalized_output(case.expected_output)
        )
        executions.append({
            "index": index,
            "case": case,
            "result": case_result,
            "passed": passed,
        })

    first_visible = next(
        (item for item in executions if not item["case"].is_hidden),
        None,
    )
    first_error = next(
        (item for item in executions if item["result"]["status"] == "error"),
        None,
    )
    first_failure = next((item for item in executions if not item["passed"]), None)

    total_runtime_ms = sum(
        item["result"].get("runtime_ms") or 0 for item in executions
    )
    display_result = dict((first_visible or executions[0])["result"])
    display_result["runtime_ms"] = total_runtime_ms
    if first_visible is None:
        display_result["stdout"] = ""
        display_result["stderr"] = ""

    if first_error is not None:
        error_case = first_error["case"]
        error_result = first_error["result"]
        display_result["status"] = "error"
        display_result["error_type"] = error_result["error_type"]
        if error_case.is_hidden:
            display_result["stderr"] = "La ejecución falló en un caso oculto."
        else:
            display_result["stdout"] = error_result["stdout"]
            display_result["stderr"] = error_result["stderr"]

    failed_case = None
    reported_failure = first_error or first_failure
    if reported_failure is not None:
        failed = reported_failure["case"]
        failed_case = (
            "Oculto"
            if failed.is_hidden
            else _normalized_output(failed.expected_output)
        )

    public_results = [
        {
            "case_number": item["index"],
            "is_hidden": bool(item["case"].is_hidden),
            "status": item["result"]["status"],
            "passed": item["passed"],
        }
        for item in executions
    ]

    return {
        "result": display_result,
        "is_correct": all(item["passed"] for item in executions),
        "failed_case": failed_case,
        "test_results": public_results,
    }

@router.post("/execute")
def execute(body: ExecuteIn, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Endpoint principal de ejecución:
    1. Ejecuta el código en un entorno controlado (Sandbox).
    2. Valida la lógica contra casos de prueba si el ejercicio existe.
    3. Registra eventos de telemetría para Learning Analytics.
    """
    storage = StorageSQLite(db)

    # Cada caso se ejecuta de forma independiente con su propia entrada.
    test_cases = storage.get_test_cases(body.exerciseId)
    evaluation = _execute_test_cases(body.code, test_cases)
    result = evaluation["result"]
    is_correct = evaluation["is_correct"]
    failed_case_info = evaluation["failed_case"]
    test_results = evaluation["test_results"]

    # 3. REGISTRO DE EVENTOS (Telemetría para la Tesis)
    
    # Evento A: Ejecución de Código (Siempre se registra)
    execution_event = Event(
        user_id=body.userId,         # ✅ CORRECCIÓN: userId
        session_id=body.sessionId,   # ✅ CORRECCIÓN: sessionId
        exercise_id=body.exerciseId, # ✅ CORRECCIÓN: exerciseId
        event="CodeExecuted",
        detector=None,
        confidence=None,
        payload={
            "attempt_id": body.attemptId, # ✅ CORRECCIÓN: attemptId
            "status": result["status"],
            "is_correct": is_correct,
            "code": body.code,
            "code_hash": hashlib.sha256(body.code.encode("utf-8")).hexdigest(),
            "lang": body.lang,
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "duration_ms": body.durationMs, # ✅ CORRECCIÓN: durationMs
            "runtime_ms": result["runtime_ms"],
            "error_type": result["error_type"],
            "failed_case": failed_case_info,
            "test_results": test_results,
        },
    )
    db.add(execution_event)

    # Evento B: Finalización (solo una vez por tarea y sesión)
    if is_correct:
        completed = (
            db.query(Event)
            .filter(
                Event.user_id == body.userId,
                Event.session_id == body.sessionId,
                Event.exercise_id == body.exerciseId,
                Event.event == "TaskCompleted",
            )
            .first()
        )
        if completed is None:
            db.add(Event(
                user_id=body.userId,
                session_id=body.sessionId,
                exercise_id=body.exerciseId,
                event="TaskCompleted",
                detector="rules",
                confidence=1.0,
                payload={
                    "attempt_id": body.attemptId,
                    "duration_ms": body.durationMs,
                    "lang": body.lang,
                },
            ))

    db.commit()

    # 3b. ACTUALIZACIÓN DEL PERFIL DE PROGRESO (happy path)
    # Se ejecuta en todo intento para que las áreas débiles reflejen los fallos.
    try:
        ProgressService(storage).update_after_attempt(
            body.userId, body.exerciseId, is_correct
        )
    except Exception as e:
        print(f"Error actualizando progreso: {e}")
        db.rollback()

    # 4. RESPUESTA AL FRONTEND
    return {
        **result,
        "is_correct": is_correct,
        "failed_case": failed_case_info,
        "test_results": test_results,
    }
