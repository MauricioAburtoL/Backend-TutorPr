# backend/app/api/cfg.py
from fastapi import APIRouter, HTTPException
from typing import Literal

# Schemas y core según la nueva estructura
from ..schemas.schemas import CFGOut, CodeIn
from ..core.cfg import build_cfg_any

router = APIRouter()

@router.post("/cfg", response_model=CFGOut)
def cfg(body: CodeIn) -> CFGOut:
    """
    Genera el CFG a partir del código y el lenguaje indicado en el body.
    body.lang debe ser: 'python' | 'java' | 'cpp'
    """
    try:
        data = build_cfg_any(body.lang, body.code)
        return CFGOut(**data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- OPCIONAL: misma operación pero con el lenguaje en el path ---
@router.post("/cfg/{lang}", response_model=CFGOut)
def cfg_by_path(lang: Literal["python", "java", "cpp"], body: CodeIn) -> CFGOut:
    """
    Variante con el lenguaje en el path: /api/cfg/python
    Ignora body.lang y usa el del path.
    """
    try:
        data = build_cfg_any(lang, body.code)
        return CFGOut(**data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
