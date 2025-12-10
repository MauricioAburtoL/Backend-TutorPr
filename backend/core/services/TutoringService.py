# backend/app/core/services/TutoringService.py
from __future__ import annotations
from typing import Any, Dict
from ..pipeline import run_detection_pipeline


class TutoringService:
    """
    Servicio de Tutoría:
    ---------------------
    - Recibe: code (str), exec_result (dict), lang (python/java/cpp)
    - Llama al pipeline de detección (reglas + extensiones futuras)
    - Devuelve un diccionario simple para la API.
    """

    def make_hint(
        self,
        code: str,
        exec_result: Dict[str, Any] | None,
        lang: str = "python"
    ) -> Dict[str, str]:

        # Normalizar entrada
        exec_result = exec_result or {}
        lang = (lang or "python").lower()

        # Pipeline devuelve un DetectionResult(dataclass)
        detection = run_detection_pipeline(code, exec_result, lang=lang)

        # Salida estandarizada para la API
        return {
            "pattern_id": detection.pattern_id,
            "concept": detection.concept,
            "hint": detection.hint,
        }
