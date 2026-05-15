from sqlalchemy import Boolean, Column, Integer, Text, JSON, TIMESTAMP, Float, Index, String, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# Importa Base desde infra 
from backend.infra.db import Base

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

    __table_args__ = (
        Index("ix_events_session", "session_id"),
        Index("ix_events_exercise", "exercise_id"),
        Index("ix_events_user", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<Event id={self.id} user={self.user_id} event={self.event} ts={self.ts}>"

# --- NUEVOS MODELOS PARA EL SISTEMA TUTOR ---

class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    icon = Column(String)
    category = Column(String)      # p.ej.: 'Fundamentos'
    total_exercises = Column(Integer, default=0)
    tags = Column(JSON)            # Lista de strings: ['Variables', 'Strings']
    estimated_time = Column(String) # p.ej.: '2h 30m'

    # Relación con ejercicios
    exercises = relationship("Exercise", back_populates="topic")

class Exercise(Base):
    __tablename__ = "exercises"
    
    id = Column(String, primary_key=True, index=True)
    topic_id = Column(String, ForeignKey("topics.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    difficulty = Column(String)    # 'Fácil' | 'Medio' | 'Difícil'
    base_code = Column(Text, default="")   # Codigo plantilla inicial
    order = Column(Integer, default=0)     # Orden dentro del topic

    topic = relationship("Topic", back_populates="exercises")

class UserStats(Base):
    """
    Este modelo es el nucleo para el perfil del usuario.
    """
    __tablename__ = "user_stats"
    
    user_id = Column(String, primary_key=True, index=True)
    username = Column(String)
    level = Column(String)          # p.ej.: "Explorador de Python"
    exercises_completed = Column(Integer, default=0)
    study_streak = Column(Integer, default=0)
    total_hours = Column(Float, default=0.0)
    
    # Datos complejos guardados como JSON para flexibilidad
    skills = Column(JSON)           # List[SkillSchema]
    last_accessed = Column(JSON)    # Objeto con exerciseId, title, etc.
    daily_tip = Column(Text)
    
    # Datos de diagnóstico para el RAG
    mastery_score = Column(Integer, default=0) # 0-100
    weak_areas = Column(JSON)       # ['Ciclos While']
    strong_areas = Column(JSON)     # ['Print']
    recommendations = Column(JSON)  # List[RecommendationSchema]
    
class TestCase(Base):
    __tablename__ = "test_cases"
    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(String, ForeignKey("exercises.id"))
    input_data = Column(String, nullable=True)  # Lo que se le envía al stdin
    expected_output = Column(String)            # Lo que se espera en el stdout
    is_hidden = Column(Boolean, default=False)  # Si el alumno puede ver este caso