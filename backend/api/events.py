from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..core.models import Event
from ..infra.db import get_db
from ..schemas import TelemetryEventIn


router = APIRouter()


@router.post("/events", status_code=status.HTTP_201_CREATED)
def create_event(body: TelemetryEventIn, db: Session = Depends(get_db)):
    """Registra acciones que nacen en la interfaz, como el inicio de una tarea."""
    event = Event(
        user_id=body.userId,
        session_id=body.sessionId,
        exercise_id=body.exerciseId,
        event=body.event,
        detector="frontend",
        confidence=1.0,
        payload=body.payload,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return {"id": event.id, "event": event.event}
