# backend/infra/storage_sqlite.py
from sqlalchemy.orm import Session
from sqlalchemy import desc # Importante para el ordenamiento
from typing import List, Optional
# Importamos los nombres exactos de tu archivo models.py
from ..core.models import Topic, Exercise, ExerciseContract, UserStats, Event

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

    def get_active_exercise_contract(
        self,
        exercise_id: str,
    ) -> Optional[ExerciseContract]:
        """Obtiene el contrato publicado más reciente de un ejercicio."""
        return (
            self.db.query(ExerciseContract)
            .filter(
                ExerciseContract.exercise_id == exercise_id,
                ExerciseContract.status == "published",
            )
            .order_by(ExerciseContract.version.desc())
            .first()
        )

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
    def get_completed_exercises(self, user_id: str) -> List[dict]:
        """
        Ejercicios que el alumno ya resolvió correctamente (hecho observable).
        Un ejercicio cuenta como completado si tiene al menos un evento CodeExecuted
        con payload.is_correct == True. Devuelve id, title y topic_id.
        """
        events = (
            self.db.query(Event)
            .filter(Event.user_id == user_id, Event.event == "CodeExecuted")
            .all()
        )
        completed_ids = {
            ev.exercise_id
            for ev in events
            if (ev.payload or {}).get("is_correct") is True
        }
        if not completed_ids:
            return []

        exercises = (
            self.db.query(Exercise)
            .filter(Exercise.id.in_(completed_ids))
            .all()
        )
        return [
            {"id": ex.id, "title": ex.title, "topic_id": ex.topic_id}
            for ex in exercises
        ]

    def count_attempts(self, user_id: str, exercise_id: str) -> int:
        """Nº de ejecuciones del alumno en un ejercicio concreto (hecho directo)."""
        return (
            self.db.query(Event)
            .filter(
                Event.user_id == user_id,
                Event.exercise_id == exercise_id,
                Event.event == "CodeExecuted",
            )
            .count()
        )

    def get_test_cases(self, exercise_id: str):
        """Consulta los casos de prueba asociados a un ejercicio específico."""
        from ..core.models import TestCase
        return (
            self.db.query(TestCase)
            .filter(TestCase.exercise_id == exercise_id)
            .order_by(TestCase.id)
            .all()
        )

