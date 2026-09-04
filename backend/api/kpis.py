from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..infra.db import get_db
from ..infra.storage_sqlite import StorageSQLite
from ..core.models import Event
from ..schemas import TopicSchema, ExerciseSchema, UserStatsSchema
from ..core.services.AnalyticsService import AnalyticsService

router = APIRouter()

# --- ENDPOINTS DE ANALYTICS ---

@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    """Calcula el porcentaje de éxito por ejercicio."""
    non_scoring = {
        "binding_inconclusive",
        "output_inconclusive",
        "configuration_error",
    }
    totals = {}
    correct = {}
    events = db.query(Event).filter(Event.event == "CodeExecuted").all()
    for event in events:
        payload = event.payload or {}
        if payload.get("evaluation_status") in non_scoring:
            continue
        totals[event.exercise_id] = totals.get(event.exercise_id, 0) + 1
        if payload.get("is_correct") is True:
            correct[event.exercise_id] = correct.get(event.exercise_id, 0) + 1

    return {
        "task_success": [
            {
                "exercise_id": exercise_id,
                "task_success_pct": correct.get(exercise_id, 0) / total * 100.0,
            }
            for exercise_id, total in totals.items()
        ]
    }

# --- ENDPOINTS DE CONTENIDO ---

@router.get("/topics", response_model=List[TopicSchema])
def get_topics(db: Session = Depends(get_db)):
    storage = StorageSQLite(db)
    return storage.get_all_topics()

@router.get(
    "/topics/{topic_id}/exercises",
    response_model=List[ExerciseSchema],
    response_model_by_alias=False,
)
def get_exercises(topic_id: str, db: Session = Depends(get_db)):
    storage = StorageSQLite(db)
    exercises = storage.get_exercises_by_topic(topic_id)
    if not exercises:
        raise HTTPException(status_code=404, detail="Tema no encontrado")
    return exercises

# 🌟 NUEVO ENDPOINT PARA EL PLAYGROUND 🌟
@router.get(
    "/exercises/{exercise_id}",
    response_model=ExerciseSchema,
    response_model_by_alias=False,
)
def get_exercise_by_id(exercise_id: str, db: Session = Depends(get_db)):
    """
    Recupera un ejercicio específico por su ID (ej: e1).
    Este es el endpoint que el Playground de Angular necesita para cargar la descripción.
    """
    storage = StorageSQLite(db)
    exercise = storage.get_exercise_by_id(exercise_id) # Asegúrate de que este método exista en StorageSQLite
    
    if not exercise:
        raise HTTPException(status_code=404, detail=f"Ejercicio {exercise_id} no encontrado")
    
    return exercise

# --- EL CORAZÓN DE TUS ANALYTICS ---

@router.get("/user/{user_id}/stats", response_model=UserStatsSchema, response_model_by_alias=False)
def get_user_stats(user_id: str, db: Session = Depends(get_db)):
    storage = StorageSQLite(db)
    stats_base = storage.get_user_stats(user_id)
    if not stats_base:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    service = AnalyticsService(storage)
    profile = service.get_structured_profile(user_id)
    return profile
