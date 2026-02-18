# backend/api/hint.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

# Rutas modulares
from ..infra.db import get_db
from ..core.services.TutoringService import TutoringService
from ..schemas import HintIn, HintOut
from ..core.models import Event

router = APIRouter()
service = TutoringService()

@router.post("/hint", response_model=HintOut)
def hint(body: HintIn, db: Session = Depends(get_db)):
    # Accedemos a través de la variable definida en la clase
    exec_data = body.execResult or {}
    
    # Validamos si la ejecución previa fue pedagógicamente correcta
    if exec_data.get("status") == "ok" and exec_data.get("is_correct") is True:
        return HintOut(
            hint="¡Tu solución ya es correcta! No necesitas más pistas.",
            pattern_id="correct",
            concept="completado"
        )
    
    # Si no es correcta, generamos la pista usando el servicio
    d = service.make_hint(body.code, exec_data, lang=(body.lang or "python").lower())

    # Registro de telemetría usando nombres camelCase
    try:
        ev = Event(
            user_id=body.userId,
            session_id=body.sessionId,
            exercise_id=body.exerciseId,
            event="FeedbackShown",
            payload={
                "attempt_id": body.attemptId,
                "pattern_id": d.get("pattern_id", "unknown"),
                "hint": d.get("hint", "")
            }
        )
        db.add(ev)
        db.commit()
    except Exception as e:
        db.rollback()

    return HintOut(
        hint=d.get("hint", ""),
        pattern_id=d.get("pattern_id", "unknown"),
        concept=d.get("concept", "")
    )