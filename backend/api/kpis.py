# backend/app/api/kpis.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func, case, cast, String

from ..infra.db import get_db          # <- ajustado a la nueva estructura
from ..core.models import Event        # <- usamos el modelo ORM

router = APIRouter()

@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    """
    Porcentaje de ejecuciones correctas (status == 'ok') por exercise_id
    considerando solo eventos 'CodeExecuted'.
    """
    # avg( CASE WHEN payload['status'] = 'ok' THEN 1 ELSE 0 END ) * 100
    ok_ratio = (
        func.avg(
            case(
                (cast(Event.payload["status"].astext, String) == "ok", 1),  # PostgreSQL/SQLite vía SQLAlchemy
                else_=0,
            )
        ) * 100.0
    ).label("task_success_pct")

    stmt = (
        select(Event.exercise_id, ok_ratio)
        .where(Event.event == "CodeExecuted")
        .group_by(Event.exercise_id)
        .order_by(Event.exercise_id)
    )

    rows = db.execute(stmt).mappings().all()
    return {"task_success": list(rows)}
