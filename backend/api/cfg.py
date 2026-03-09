# backend/api/cfg.py
import re
from fastapi import APIRouter, HTTPException

# Schemas y core
from ..schemas import CFGOut, CFGRequest, CodeOnly, Lang
from ..core.cfg import build_cfg_any
from ..core.services.gemini_orchestrator import get_or_fetch

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


@router.post("/cfg", response_model=CFGOut)
def cfg(body: CFGRequest) -> CFGOut:
    """
    Genera diagrama de flujo (CFG). Si se proporcionan userId y exerciseId,
    intenta usar el mermaid generado por Gemini desde cache.
    Valida el mermaid antes de usarlo; si es invalido, cae al fallback AST.
    """
    # 1. Si hay contexto de usuario, intentar cache de Gemini
    if body.userId and body.exerciseId:
        try:
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
        return CFGOut(**data, source="ast")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cfg/{lang}", response_model=CFGOut)
def cfg_by_path(lang: Lang, body: CodeOnly) -> CFGOut:
    """
    Variante con el lenguaje en el path: /api/cfg/python
    El body solo incluye { "code": "..." }.
    Sin cache de Gemini (no tiene contexto de usuario).
    """
    try:
        data = build_cfg_any(lang, body.code)
        return CFGOut(**data, source="ast")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
