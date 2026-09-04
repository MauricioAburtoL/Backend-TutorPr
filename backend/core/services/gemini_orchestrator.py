# backend/core/services/gemini_orchestrator.py
import threading
from typing import Dict
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
    student_context: str = "",
    evaluation_status: str = None,
    program_output: str = "",
    program_error: str = "",
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
        student_context: Perfil del estudiante en hechos directos
        evaluation_status: Veredicto ya emitido por el evaluador
        program_output: Consola visible producida por el programa
        program_error: Error reportado durante la ejecucion

    Returns:
        CacheEntry con la respuesta de Gemini y el estado de entrega de hints

    La clave de caché sigue siendo el código: para un mismo ejercicio, el mismo
    código produce siempre la misma evaluación, así que el contexto añadido no
    introduce variantes que la caché deba distinguir.
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
            evaluationStatus=evaluation_status,
            programOutput=program_output,
            programError=program_error,
        )
        response = _gemini_service.analyze_code(request)
        return gemini_cache.put(user_id, exercise_id, code, response)
