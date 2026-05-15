# backend/infra/storage_sqlite.py
from sqlalchemy.orm import Session
from sqlalchemy import desc # Importante para el ordenamiento
from typing import List, Optional
# Importamos los nombres exactos de tu archivo models.py
from ..core.models import Topic, Exercise, UserStats, Event 
from ..schemas import TopicSchema, ExerciseSchema, UserStatsSchema

class StorageSQLite:
    def __init__(self, db: Session):
        self.db = db

    # --- Lógica de Temas (Topics) ---
    def get_all_topics(self) -> List[Topic]:
        """Retorna todos los temas disponibles en la plataforma."""
        return self.db.query(Topic).all()

    def get_topic_by_id(self, topic_id: str) -> Optional[Topic]:
        """Busca un tema específico por su ID único."""
        return self.db.query(Topic).filter(Topic.id == topic_id).first()

    # --- Lógica de Ejercicios (Exercises) ---
    def get_exercises_by_topic(self, topic_id: str) -> List[Exercise]:
        """Obtiene la lista de ejercicios asociados a un tema, ordenados."""
        return self.db.query(Exercise).filter(Exercise.topic_id == topic_id).order_by(Exercise.order).all()

    def get_exercise_by_id(self, exercise_id: str) -> Optional[Exercise]:
        """Busca un ejercicio específico."""
        return self.db.query(Exercise).filter(Exercise.id == exercise_id).first()

    # --- Lógica de Usuario y Analytics ---
    def get_user_stats(self, user_id: str) -> Optional[UserStats]:
        """Recupera el perfil de progreso y habilidades del estudiante."""
        return self.db.query(UserStats).filter(UserStats.user_id == user_id).first()

    # ⬇️ NUEVO MÉTODO: Esta es la pieza que faltaba para tu AnalyticsService
    def get_recent_events(self, user_id: str, limit: int = 30) -> List[Event]:
        """
        Recupera los eventos más recientes del usuario.
        Esta es la 'evidencia cruda' que el AnalyticsService usará para calcular
        la probabilidad de bloqueo (stuckProbability).
        """
        return (
            self.db.query(Event)
            .filter(Event.user_id == user_id)
            .order_by(desc(Event.id)) # Traemos los más recientes primero
            .limit(limit)
            .all()
        )
    def get_test_cases(self, exercise_id: str):
        """Consulta los casos de prueba asociados a un ejercicio específico."""
        from ..core.models import TestCase
        return self.db.query(TestCase).filter(TestCase.exercise_id == exercise_id).all()

    def get_exercise_by_id(self, exercise_id: str):
        """Consulta la tabla 'exercises' por ID."""
        from ..core.models import Exercise # Asegúrate de importar tu modelo
        return self.db.query(Exercise).filter(Exercise.id == exercise_id).first()

    def create_event(self, event_data: dict) -> Event:
        """Registra un evento de interacción (ej. ejecución de código) para telemetría."""
        db_event = Event(**event_data)
        self.db.add(db_event)
        self.db.commit()
        self.db.refresh(db_event)
        return db_event

    def update_user_progress(self, user_id: str, success: bool):
        """
        Actualiza los contadores de progreso del usuario.
        """
        stats = self.get_user_stats(user_id)
        if stats:
            if success:
                stats.exercises_completed += 1 
            
            self.db.commit()
            self.db.refresh(stats)
        return stats