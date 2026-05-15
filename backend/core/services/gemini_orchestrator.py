# backend/core/services/gemini_orchestrator.py
from typing import List, Dict, Any
from backend.schemas.geminiSchemas import AssistRequest
from backend.core.services.GeminiTutoringService import GeminiTutoringService
from backend.core.services.gemini_cache import gemini_cache, CacheEntry

# Singleton del servicio Gemini
_gemini_service = GeminiTutoringService()


def get_or_fetch(
    user_id: str,
    exercise_id: str,
    code: str,
    language: str,
    context: str = "",
    static_errors: List[Dict[str, Any]] = None,
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
    # 1. Buscar en cache
    entry = gemini_cache.get(user_id, exercise_id, code)
    if entry is not None:
        return entry

    # 2. Cache miss -> llamar a Gemini
    request = AssistRequest(
        context=context or f"Exercise {exercise_id}",
        language=language,
        studentCode=code,
    )
    response = _gemini_service.analyze_code(request, static_errors=static_errors)

    # 3. Guardar en cache y retornar
    entry = gemini_cache.put(user_id, exercise_id, code, response)
    return entry
