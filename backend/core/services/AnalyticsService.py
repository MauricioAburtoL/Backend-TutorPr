# backend/core/services/AnalyticsService.py
from typing import List, Dict, Any, Optional
from ...schemas import BehavioralMetrics, UserStatsSchema

class AnalyticsService:
    def __init__(self, storage):
        """
        El storage es tu clase StorageSQLite que ya maneja 
        la persistencia y cálculos básicos de KPIs.
        """
        self.storage = storage

    def get_structured_profile(self, user_id: str) -> UserStatsSchema:
        """
        Calcula un perfil de aprendizaje estructurado.
        Convierte el modelo de SQLAlchemy a Pydantic antes de inyectar los analytics.
        """
        # 1. Recuperamos el objeto de la DB
        user_stats_db = self.storage.get_user_stats(user_id)
        if not user_stats_db:
            return None

        # 2. Recuperamos eventos para el cálculo de comportamiento
        events = self.storage.get_recent_events(user_id, limit=30)
        behavioral = self._calculate_behavioral_metrics(events)

        # 3. CONVERSIÓN CRÍTICA: 
        # Usamos model_validate para convertir el objeto SQLAlchemy a un diccionario de Pydantic
        # Esto evita el TypeError: 'UserStats' object does not support item assignment
        stats_data = UserStatsSchema.model_validate(user_stats_db).model_dump()
        
        # 4. Ahora stats_data SI es un diccionario y permite asignación
        stats_data["behavioral_profile"] = behavioral
        
        # 5. Si añadiste avgResolutionTime al Service, calcúlalo aquí también
        #stats_data["avgResolutionTime"] = self._calculate_avg_time(events)

        return UserStatsSchema(**stats_data)
    
    
    def get_prompt_context(self, user_id: str, exercise_id: str) -> str:
        """
        Construye un bloque de contexto para inyectar al prompt del tutor.
        SOLO hechos directos y trazables (sin porcentajes ni inferencias):
        ejercicios completados, áreas débiles/fuertes, error más frecuente y
        nº de intentos en el ejercicio actual.
        Devuelve "" si el alumno no tiene perfil (degradación elegante).
        """
        profile = self.get_structured_profile(user_id)
        if not profile:
            return ""

        completed = self.storage.get_completed_exercises(user_id)
        attempts = self.storage.count_attempts(user_id, exercise_id)

        lines = ["PERFIL DEL ESTUDIANTE (usar para calibrar la ayuda, NO para revelar la solución):"]

        if completed:
            titles = ", ".join(f'"{c["title"]}"' for c in completed)
            lines.append(f"- Ya completó: {titles} ({len(completed)} ejercicios)")

        weak = profile.weakAreas or []
        strong = profile.strongAreas or []
        if weak or strong:
            weak_txt = ", ".join(weak) if weak else "—"
            strong_txt = ", ".join(strong) if strong else "—"
            lines.append(f"- Áreas débiles: {weak_txt} | Fuertes: {strong_txt}")

        behavioral = profile.behavioralProfile
        if behavioral and behavioral.mostCommonErrorType:
            lines.append(f"- Error más frecuente: {behavioral.mostCommonErrorType}")

        if attempts > 0:
            lines.append(f"- Lleva {attempts} intento(s) en este ejercicio")

        # Si solo está el encabezado, no hay nada útil que inyectar.
        if len(lines) == 1:
            return ""

        lines.append(
            "Instrucción: refuerza las áreas débiles; apóyate en lo que ya domina; "
            "si lleva varios intentos, sé más concreto. Mantén la guía socrática, sin dar la solución."
        )
        return "\n".join(lines)

    def _calculate_behavioral_metrics(self, events: List[Any]) -> BehavioralMetrics:
        """
        Lógica interna para transformar eventos crudos en indicadores pedagógicos.
        """
        if not events:
            return BehavioralMetrics()

        error_counts: Dict[str, int] = {}
        hint_requests = 0
        successes = 0
        total_attempts = 0
        
        # Análisis de la racha de errores para detectar bloqueos (Struggle)
        consecutive_errors = 0
        max_consecutive_errors = 0

        for ev in events:
            payload = ev.payload or {}
            
            if ev.event == "CodeExecuted":
                total_attempts += 1
                if payload.get("status") == "error":
                    # Conteo por tipo de error
                    err = payload.get("error_type", "UnknownError")
                    error_counts[err] = error_counts.get(err, 0) + 1
                    
                    # Lógica de racha de errores
                    consecutive_errors += 1
                    max_consecutive_errors = max(max_consecutive_errors, consecutive_errors)
                else:
                    successes += 1
                    consecutive_errors = 0 # Reset de racha al tener éxito
            
            if ev.event == "FeedbackShown":
                hint_requests += 1

        # --- Cálculos Finales ---
        
        # Error más frecuente
        main_error = max(error_counts, key=error_counts.get) if error_counts else None
        
        # Ratio de ayuda: ¿Cuántas pistas pide por cada éxito?
        hint_ratio = hint_requests / successes if successes > 0 else hint_requests
        
        # Promedio de intentos (basado en la muestra de eventos)
        # Dividimos por un estimado de ejercicios únicos en la muestra
        unique_exercises = len(set(ev.exercise_id for ev in events))
        avg_attempts = total_attempts / unique_exercises if unique_exercises > 0 else 0

        # Cálculo de Probabilidad de Bloqueo (Stuck Probability)
        # Se escala si hay muchos errores consecutivos o un ratio de ayuda muy alto
        stuck_prob = 0.0
        if max_consecutive_errors >= 3: stuck_prob += 0.4
        if hint_ratio > 2: stuck_prob += 0.3
        if len(error_counts) == 1 and total_attempts > 3: stuck_prob += 0.2 # Mismo error repetido
        
        return BehavioralMetrics(
            avg_attempts_per_exercise=round(avg_attempts, 2),
            hints_per_success_ratio=round(hint_ratio, 2),
            most_common_error_type=main_error,
            stuck_probability=min(stuck_prob, 1.0)
        )