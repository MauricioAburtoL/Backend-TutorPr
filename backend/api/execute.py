# backend/app/api/execute.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..infra.db import get_db
from ..core.models import Event
from ..schemas import ExecuteIn
from ..core.services.ExecutionService import run_code_sandboxed

router = APIRouter()

@router.post("/execute")
def execute(body: ExecuteIn, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Endpoint del execute: delega toda la lógica en ExecutionService
    y registra el evento.
    """

    result = run_code_sandboxed(body.code)

    # --- guardar evento ---
    ev = Event(
        user_id=body.user_id,
        session_id=body.session_id,
        exercise_id=body.exercise_id,
        event="CodeExecuted",
        detector=None,
        confidence=None,
        payload={
            "attempt_id": body.attempt_id,
            "status": result["status"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "error_type": result["error_type"],
        },
    )
    db.add(ev)
    db.commit()

    return result
