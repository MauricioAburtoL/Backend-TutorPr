# backend/core/services/gemini_orchestrator.py
import threading
from typing import List, Dict, Any
from backend.schemas.geminiSchemas import AssistRequest
from backend.core.services.GeminiTutoringService import GeminiTutoringService
from backend.core.services.gemini_cache import gemini_cache, CacheEntry

# Singleton del servicio Gemini
_gemini_service = GeminiTutoringService()
_request_locks: Dict[tuple[str, str], threading.Lock] = {}
_request_locks_guard = threading.Lock()


def _request_lock(user_id: str, exercise_id: str) -> threading.Lock:
    """Comparte una sola llamada en curso por usuario y ejercicio."""
    key = (user_id, exercise_id)
    with _request_locks_guard:
        return _request_locks.setdefault(key, threading.Lock())


def get_or_fetch(
    user_id: str,
    exercise_id: str,
    code: str,
    language: str,
    context: str = "",
    static_errors: List[Dict[str, Any]] = None,
    student_context: str = "",
) -> CacheEntry:
    """
    Retorna la respuesta cacheada de Gemini para esta combinacion user/exercise/code.
    Si no esta cacheada o es stale, llama a Gemini una sola vez y cachea el resultado.

    Args:
        user_id: ID del usuario/estudiante
        exercise_id: ID del ejercicio
        code: Codigo fuente del estudiante
        language: Lenguaje de programacion (python, javascript, etc.)
        context: Contexto del ejercicio (descripcion, instrucciones)
        static_errors: Errores detectados por analisis estatico (compilador)

    Returns:
        CacheEntry con la respuesta de Gemini y el estado de entrega de hints
    """
    # El segundo chequeo dentro del lock evita que dos clics simultáneos hagan
    # dos llamadas externas antes de que la primera alcance a llenar la caché.
    with _request_lock(user_id, exercise_id):
        entry = gemini_cache.get(user_id, exercise_id, code)
        if entry is not None:
            return entry

        request = AssistRequest(
            context=context or f"Exercise {exercise_id}",
            language=language,
            studentCode=code,
            studentContext=student_context,
        )
        response = _gemini_service.analyze_code(request, static_errors=static_errors)
        return gemini_cache.put(user_id, exercise_id, code, response)
