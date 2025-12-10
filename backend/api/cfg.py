# backend/app/api/cfg.py
from fastapi import APIRouter, HTTPException

# Schemas y core según la nueva estructura
from ..schemas.schemas import CFGOut, CodeIn, CodeOnly, Lang
from ..core.cfg import build_cfg_any

router = APIRouter()

@router.post("/cfg", response_model=CFGOut)
def cfg(body: CodeIn) -> CFGOut:
    """
    Variante con lang en el body. 'body.lang' ya trae el default 'python'
    desde el schema, así que no hay que forzarlo aquí.
    """
    try:
        data = build_cfg_any(body.lang, body.code)
        return CFGOut(**data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cfg/{lang}", response_model=CFGOut)
def cfg_by_path(lang: Lang, body: CodeOnly) -> CFGOut:
    """
    Variante con el lenguaje en el path: /api/cfg/python
    El body sólo incluye { "code": "..." }.
    """
    try:
        data = build_cfg_any(lang, body.code)
        return CFGOut(**data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
