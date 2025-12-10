# backend/api/hint.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# ⬇️ Rutas nuevas según la estructura modular
from ..infra.db import get_db
from ..core.services.TutoringService import TutoringService

# Si tus Pydantic siguen en backend/schemas/schemas.py:
from ..schemas.schemas import HintIn, HintOut

# Si tu modelo Event quedó en core/models.py:
from ..core.models import Event
# (Si lo dejaste en otro sitio, ajusta el import acorde)

router = APIRouter()
service = TutoringService()

@router.post("/hint", response_model=HintOut)
def hint(body: HintIn, db: Session = Depends(get_db)):
    """
    Genera una pista a partir del código, el resultado de ejecución y el lenguaje.
    - Usa el servicio de tutoría (pipeline + detectores).
    - Registra el evento en la base de datos.
    """
    # Normaliza acceso a exec_result (puede llegar como dict o modelo Pydantic)
    exec_result = {}
    if body.exec_result:
        # Pydantic model -> dict
        try:
            exec_result = body.exec_result.dict()
        except AttributeError:
            # Ya es dict
            exec_result = dict(body.exec_result)

    # Lenguaje (por defecto Python si no viene)
    lang = (getattr(body, "lang", None) or "python").lower()

    # Si la última ejecución fue correcta, responde OK directo
    if exec_result.get("status") == "ok":
        d = {"pattern_id": "correct", "concept": "", "hint": "Tu solución es correcta."}
    else:
        d = service.make_hint(body.code, exec_result, lang=lang)

    # Log de evento (opcional pero útil para LA/KPIs)
    try:
        ev = Event(
            user_id=body.user_id,
            session_id=body.session_id,
            exercise_id=body.exercise_id,
            event="FeedbackShown",
            detector="rules",             # o "pipeline" si quieres reflejar la capa
            confidence=1.0,
            payload={
                "attempt_id": body.attempt_id,
                "pattern_id": d.get("pattern_id", "unknown"),
                "hint": d.get("hint", ""),
                "concept": d.get("concept", ""),
                "lang": lang,
            },
        )
        db.add(ev)
        db.commit()
    except Exception:
        db.rollback()  # no tires el endpoint si el log falla

    return HintOut(
        hint=d.get("hint", ""),
        pattern_id=d.get("pattern_id", "unknown"),
        concept=d.get("concept", ""),
    )
