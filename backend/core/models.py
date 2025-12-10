# backend/app/core/models.py
from sqlalchemy import Column, Integer, Text, JSON, TIMESTAMP, Float, Index
from sqlalchemy.sql import func

# Importa Base desde infra (ajuste clave)
from ..infra.db import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ts = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    user_id = Column(Text, nullable=False)
    session_id = Column(Text, nullable=False)
    exercise_id = Column(Text, nullable=False)

    event = Column(Text, nullable=False)         # p.ej.: CodeExecuted, FeedbackShown
    detector = Column(Text)                      # p.ej.: 'rules', 'llm', 'static'
    confidence = Column(Float)                   # 0.0 – 1.0
    payload = Column(JSON, nullable=False)       # dict arbitrario con detalles

    # Índices adicionales útiles para queries por sesión/ejercicio/usuario
    __table_args__ = (
        Index("ix_events_session", "session_id"),
        Index("ix_events_exercise", "exercise_id"),
        Index("ix_events_user", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<Event id={self.id} user={self.user_id} event={self.event} ts={self.ts}>"
