# backend/api/cfg.py
import hashlib
import re
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Schemas y core
from ..schemas import CFGOut, CFGRequest, CodeOnly, Lang
from ..core.cfg import build_cfg_any
from ..core.code_validation import has_meaningful_code
from ..core.services.gemini_orchestrator import get_or_fetch
from ..core.services.gemini_cache import gemini_cache
from ..core.models import Event
from ..infra.db import get_db

router = APIRouter()

# Palabras clave validas para iniciar un diagrama Mermaid
_MERMAID_VALID_STARTS = re.compile(
    r"^\s*(flowchart|graph|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|gitGraph)",
    re.IGNORECASE,
)


def _is_valid_mermaid(src: str) -> bool:
    """Validacion basica de sintaxis Mermaid: debe iniciar con un tipo de diagrama valido."""
    if not src or not src.strip():
        return False
    return bool(_MERMAID_VALID_STARTS.match(src.strip()))


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
    Genera diagrama de flujo (CFG). Si se proporcionan userId y exerciseId,
    intenta usar el mermaid generado por Gemini desde cache.
    Valida el mermaid antes de usarlo; si es invalido, cae al fallback AST.
    """
    started_at = time.perf_counter()

    # 1. Si hay contexto de usuario, intentar cache de Gemini
    if body.userId and body.exerciseId:
        try:
            cache_hit = gemini_cache.get(body.userId, body.exerciseId, body.code) is not None
            entry = get_or_fetch(
                user_id=body.userId,
                exercise_id=body.exerciseId,
                code=body.code,
                language=(body.lang or "python").lower(),
            )
            # Solo ignorar el mermaid si es un fallo de sistema real, no si el alumno tiene errores
            is_system_failure = (
                entry.response.status == "error"
                and entry.response.pedagogicalFeedback.startswith("System Error:")
            )
            gemini_mermaid = "" if is_system_failure else (entry.response.mermaidChart or "")

            if gemini_mermaid and _is_valid_mermaid(gemini_mermaid):
                source = "cache" if cache_hit else "gemini"
                _record_cfg_event(
                    db,
                    body,
                    source=source,
                    success=True,
                    started_at=started_at,
                )
                return CFGOut(
                    language=body.lang or "python",
                    nodes=[],
                    edges=[],
                    mermaid=gemini_mermaid,
                    source="gemini",
                )
        except Exception:
            pass  # Fallback a CFG basado en AST

    # 2. Fallback: CFG basado en AST (logica original)
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
