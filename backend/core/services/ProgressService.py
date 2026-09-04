# backend/core/services/ProgressService.py
from typing import Dict, Set
from ..models import Event, Exercise, Topic, UserStats


class ProgressService:
    """
    Actualiza el perfil de progreso del estudiante tras cada intento.
    Todas las señales se derivan de hechos observables (eventos CodeExecuted),
    con reglas operacionales explícitas — defendibles metodológicamente.
    """

    def __init__(self, storage):
        # storage es StorageSQLite; usamos su sesión para consultas/escritura.
        self.storage = storage
        self.db = storage.db

    _NON_SCORING_STATUSES = {
        "binding_inconclusive",
        "output_inconclusive",
        "configuration_error",
    }

    def update_after_attempt(self, user_id: str, exercise_id: str, is_correct: bool) -> None:
        if not user_id:
            return

        stats = self._get_or_create_stats(user_id)

        events = (
            self.db.query(Event)
            .filter(Event.user_id == user_id, Event.event == "CodeExecuted")
            .all()
        )

        scored_events = [
            event
            for event in events
            if (event.payload or {}).get("evaluation_status")
            not in self._NON_SCORING_STATUSES
        ]

        # --- Ejercicios completados (distinct con is_correct=True) ---
        completed_ids: Set[str] = {
            ev.exercise_id
            for ev in scored_events
            if (ev.payload or {}).get("is_correct") is True
        }
        stats.exercises_completed = len(completed_ids)

        # --- Mapa ejercicio -> tema ---
        attempted_ex_ids = {ev.exercise_id for ev in scored_events}
        ex_to_topic: Dict[str, str] = {}
        if attempted_ex_ids:
            for ex in self.db.query(Exercise).filter(Exercise.id.in_(attempted_ex_ids)).all():
                ex_to_topic[ex.id] = ex.topic_id

        # --- Áreas fuertes / débiles por tema (regla operacional) ---
        # Fuerte: tema con >=1 ejercicio resuelto.
        # Débil: tema con intentos fallidos y AÚN sin ningún ejercicio resuelto.
        solved_topics: Set[str] = {ex_to_topic.get(eid) for eid in completed_ids}
        solved_topics.discard(None)

        failed_topics: Set[str] = set()
        for ev in scored_events:
            if (ev.payload or {}).get("is_correct") is not True:
                t = ex_to_topic.get(ev.exercise_id)
                if t:
                    failed_topics.add(t)
        weak_topics = {t for t in failed_topics if t not in solved_topics}

        topic_titles = self._topic_titles(solved_topics | weak_topics)
        stats.strong_areas = sorted(topic_titles[t] for t in solved_topics if t in topic_titles)
        stats.weak_areas = sorted(topic_titles[t] for t in weak_topics if t in topic_titles)

        # --- Tasa de aciertos (solo para la UI; NO se inyecta al prompt) ---
        total = len(scored_events)
        correct = sum(
            1
            for ev in scored_events
            if (ev.payload or {}).get("is_correct") is True
        )
        stats.mastery_score = round(correct / total * 100) if total > 0 else 0

        # --- Último ejercicio accedido ---
        current = self.db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if current:
            topic = self.db.query(Topic).filter(Topic.id == current.topic_id).first()
            stats.last_accessed = {
                "exercise_id": current.id,
                "title": current.title,
                "topic_name": topic.title if topic else current.topic_id,
                "progress": 100 if is_correct else 0,
            }

        self.db.commit()

    def _get_or_create_stats(self, user_id: str) -> UserStats:
        stats = self.db.query(UserStats).filter(UserStats.user_id == user_id).first()
        if stats:
            return stats
        stats = UserStats(
            user_id=user_id,
            username=user_id,
            level="Explorador de Python",
            exercises_completed=0,
            study_streak=0,
            total_hours=0.0,
            skills=[],
            last_accessed=None,
            daily_tip="Practica un poco cada dia para mantener tu racha.",
            mastery_score=0,
            weak_areas=[],
            strong_areas=[],
            recommendations=[],
        )
        self.db.add(stats)
        return stats

    def _topic_titles(self, topic_ids: Set[str]) -> Dict[str, str]:
        if not topic_ids:
            return {}
        topics = self.db.query(Topic).filter(Topic.id.in_(topic_ids)).all()
        return {t.id: t.title for t in topics}
