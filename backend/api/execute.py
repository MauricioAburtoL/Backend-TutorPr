# backend/app/api/execute.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

# Importaciones de la capa de infraestructura y núcleo
from ..infra.db import get_db
from ..infra.storage_sqlite import StorageSQLite
from ..core.models import Event
from ..schemas import ExecuteIn
from ..core.services.ExecutionService import run_code_sandboxed, validate_logic

router = APIRouter()

@router.post("/execute")
def execute(body: ExecuteIn, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Endpoint principal de ejecución:
    1. Ejecuta el código en un entorno controlado (Sandbox).
    2. Valida la lógica contra casos de prueba si el ejercicio existe.
    3. Registra eventos de telemetría para Learning Analytics.
    """
    storage = StorageSQLite(db)
    
    # 1. EJECUCIÓN TÉCNICA
    result = run_code_sandboxed(body.code)
    
    # 2. VALIDACIÓN PEDAGÓGICA (Basada en comportamiento)
    is_correct = False
    failed_case_info = None
    
    # ✅ CORRECCIÓN: body.exerciseId (en lugar de exercise_id)
    if result["status"] == "ok" and body.exerciseId:
        # Recuperamos los casos de prueba de la base de datos
        test_cases = storage.get_test_cases(body.exerciseId)
        
        # Comparamos la salida real contra la esperada
        val_result = validate_logic(result["stdout"], test_cases)
        is_correct = val_result["is_correct"]
        failed_case_info = val_result["failed_case"]

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
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "duration_ms": body.durationMs, # ✅ CORRECCIÓN: durationMs
            "error_type": result["error_type"],
            "failed_case": failed_case_info
        },
    )
    db.add(execution_event)

    # Evento B: Feedback (Solo si la solución es pedagógicamente correcta)
    if is_correct:
        feedback_event = Event(
            user_id=body.userId,         # ✅ CORRECCIÓN: userId
            session_id=body.sessionId,   # ✅ CORRECCIÓN: sessionId
            exercise_id=body.exerciseId, # ✅ CORRECCIÓN: exerciseId
            event="FeedbackShown",
            detector="rules",
            confidence=1.0,
            payload={
                "attempt_id": body.attemptId, # ✅ CORRECCIÓN: attemptId
                "pattern_id": "correct",
                "hint": "Tu solución es correcta.",
                "lang": "python"
            }
        )
        db.add(feedback_event)

    db.commit()

    # 4. RESPUESTA AL FRONTEND
    return {
        **result,
        "is_correct": is_correct,
        "failed_case": failed_case_info
    }