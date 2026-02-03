from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func, case, cast, String
from typing import List

from ..infra.db import get_db
from ..infra.storage_sqlite import StorageSQLite
from ..core.models import Event
from ..schemas import TopicSchema, ExerciseSchema, UserStatsSchema

# ⬇️ NUEVO: Importamos el servicio para que deje de salir el error de Pylance
from ..core.services.AnalyticsService import AnalyticsService

router = APIRouter()

# --- ENDPOINTS DE ANALYTICS ---

@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    """
    Calcula el porcentaje de éxito por ejercicio.
    Útil para los 'Learning Analytics' de tu investigación.
    """
    ok_ratio = (
        func.avg(
            case(
                (cast(Event.payload["status"].astext, String) == "ok", 1),
                else_=0,
            )
        ) * 100.0
    ).label("task_success_pct")

    stmt = (
        select(Event.exercise_id, ok_ratio)
        .where(Event.event == "CodeExecuted")
        .group_by(Event.exercise_id)
    )

    rows = db.execute(stmt).mappings().all()
    return {"task_success": list(rows)}

# --- ENDPOINTS DE CONTENIDO ---

@router.get("/topics", response_model=List[TopicSchema])
def get_topics(db: Session = Depends(get_db)):
    storage = StorageSQLite(db)
    return storage.get_all_topics()

@router.get("/topics/{topic_id}/exercises", response_model=List[ExerciseSchema])
def get_exercises(topic_id: str, db: Session = Depends(get_db)):
    storage = StorageSQLite(db)
    exercises = storage.get_exercises_by_topic(topic_id)
    if not exercises:
        raise HTTPException(status_code=404, detail="Tema no encontrado")
    return exercises

# --- EL CORAZÓN DE TUS ANALYTICS (Corregido) ---

@router.get("/user/{user_id}/stats", response_model=UserStatsSchema, response_model_by_alias=False)
def get_user_stats(user_id: str, db: Session = Depends(get_db)):
    """
    Endpoint clave: Entrega el perfil de usuario procesado por el AnalyticsService.
    """
    storage = StorageSQLite(db)
    
    # Verificamos primero si el usuario existe en los registros base
    stats_base = storage.get_user_stats(user_id)
    if not stats_base:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # ⬇️ USAMOS EL SERVICIO: Aquí es donde ocurre el cálculo de comportamiento
    service = AnalyticsService(storage)
    
    # Llamamos al nuevo método que integra KPIs + Comportamiento
    profile = service.get_structured_profile(user_id)
    
    return profile