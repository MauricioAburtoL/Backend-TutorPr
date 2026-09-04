# backend/core/services/gemini_cache.py
import hashlib
import threading
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from backend.schemas.geminiSchemas import AssistResponse


@dataclass
class CacheEntry:
    """
    Guarda una respuesta cacheada de Gemini y rastrea la entrega progresiva de hints.

    Orden de entrega progresiva:
      0 -> pedagogical_feedback
      1..N -> technical_hints[0..N-1]
      N+1 -> next_step_question
    """
    response: AssistResponse
    code_hash: str
    hint_index: int = 0

    def next_hint(self) -> Tuple[str, bool]:
        """
        Retorna la siguiente pista progresiva y si quedan mas.
        Returns:
            (hint_text, has_more)
        """
        total_steps = 1 + len(self.response.technicalHints) + 1
        current = self.hint_index

        if current == 0:
            text = self.response.pedagogicalFeedback
        elif current <= len(self.response.technicalHints):
            text = self.response.technicalHints[current - 1]
        elif current == len(self.response.technicalHints) + 1:
            text = self.response.nextStepQuestion
        else:
            # Todas las pistas agotadas, repite la ultima
            text = self.response.nextStepQuestion
            return text, False

        self.hint_index = min(current + 1, total_steps)
        has_more = self.hint_index < total_steps
        return text, has_more


# Tipo alias para la llave del cache
CacheKey = Tuple[str, str]  # (user_id, exercise_id)


class GeminiCache:
    """Cache en memoria thread-safe para respuestas de Gemini."""

    def __init__(self):
        self._store: Dict[CacheKey, CacheEntry] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _hash_code(code: str) -> str:
        return hashlib.sha256(code.strip().encode("utf-8")).hexdigest()

    def get(self, user_id: str, exercise_id: str, code: str) -> Optional[CacheEntry]:
        """Retorna la entry cacheada solo si el hash del codigo coincide (no es stale)."""
        key = (user_id, exercise_id)
        code_hash = self._hash_code(code)
        with self._lock:
            entry = self._store.get(key)
            if entry and entry.code_hash == code_hash:
                return entry
            return None

    def put(self, user_id: str, exercise_id: str, code: str, response: AssistResponse) -> CacheEntry:
        """Almacena una nueva respuesta de Gemini, reemplazando cualquier entry previa."""
        key = (user_id, exercise_id)
        code_hash = self._hash_code(code)
        entry = CacheEntry(response=response, code_hash=code_hash, hint_index=0)
        with self._lock:
            self._store[key] = entry
        return entry

    def invalidate(self, user_id: str, exercise_id: str) -> None:
        """Elimina explicitamente una entry del cache."""
        key = (user_id, exercise_id)
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        """Limpia todas las entries del cache."""
        with self._lock:
            self._store.clear()


# Singleton a nivel de modulo
gemini_cache = GeminiCache()
