# backend/api/cfg.py
import hashlib
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Schemas y core
from ..schemas import CFGOut, CFGRequest, CodeOnly, Lang
from ..core.cfg import build_cfg_any
from ..core.code_validation import differs_from_initial_code, has_meaningful_code
from ..core.models import Event, Exercise
from ..infra.db import get_db

router = APIRouter()

def _record_cfg_event(
    db: Session,
    body: CFGRequest,
    *,
    source: str,
    success: bool,
    started_at: float,
    error: str | None = None,
) -> None:
    if not body.userId or not body.sessionId or not body.exerciseId:
        return

    db.add(Event(
        user_id=body.userId,
        session_id=body.sessionId,
        exercise_id=body.exerciseId,
        event="CFGViewed",
        detector=source,
        confidence=1.0 if success else 0.0,
        payload={
            "attempt_id": body.attemptId,
            "source": source,
            "success": success,
            "latency_ms": round((time.perf_counter() - started_at) * 1000, 2),
            "code_hash": hashlib.sha256(body.code.encode("utf-8")).hexdigest(),
            "error": error,
        },
    ))
    db.commit()


@router.post("/cfg", response_model=CFGOut)
def cfg(body: CFGRequest, db: Session = Depends(get_db)) -> CFGOut:
    """
    Genera un CFG exclusivamente a partir del código recibido.

    Gemini no participa en este flujo: así el diagrama nunca completa ni infiere
    una solución que el estudiante no escribió y cada nodo conserva sus líneas.
    """
    started_at = time.perf_counter()

    if body.exerciseId:
        exercise = db.query(Exercise).filter(Exercise.id == body.exerciseId).first()
        if exercise and not differs_from_initial_code(
            body.code,
            exercise.base_code or "",
            body.lang,
        ):
            message = "Modifica el código inicial antes de generar el diagrama."
            _record_cfg_event(
                db,
                body,
                source="validation",
                success=False,
                started_at=started_at,
                error=message,
            )
            raise HTTPException(status_code=422, detail=message)

    try:
        data = build_cfg_any(body.lang, body.code)
        _record_cfg_event(
            db,
            body,
            source="ast",
            success=True,
            started_at=started_at,
        )
        return CFGOut(**data, source="ast")
    except ValueError as e:
        _record_cfg_event(
            db,
            body,
            source="ast",
            success=False,
            started_at=started_at,
            error=str(e),
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cfg/{lang}", response_model=CFGOut)
def cfg_by_path(lang: Lang, body: CodeOnly) -> CFGOut:
    """
    Variante con el lenguaje en el path: /api/cfg/python
    El body solo incluye { "code": "..." }.
    Sin cache de Gemini (no tiene contexto de usuario).
    """
    if not has_meaningful_code(body.code, lang):
        raise HTTPException(
            status_code=422,
            detail="Escribe alguna instrucción antes de generar el diagrama.",
        )

    try:
        data = build_cfg_any(lang, body.code)
        return CFGOut(**data, source="ast")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
