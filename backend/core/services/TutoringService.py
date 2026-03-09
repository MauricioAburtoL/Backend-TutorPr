# backend/app/core/services/TutoringService.py
import re # Necesario para limpiar comentarios
from typing import Any, Dict, List
from ..pipeline import run_detection_pipeline

class TutoringService:
    
    """
    Servicio de Tutoría:
    ---------------------
    - Recibe: code (str), exec_result (dict), lang (python/java/cpp)
    - Llama al pipeline de detección (reglas + extensiones futuras)
    - Devuelve un diccionario simple para la API.
    """
    
    def _is_empty_or_only_comments(self, code: str) -> bool:
        """Heurística para detectar si el alumno realmente escribió lógica."""
        # Elimina comentarios de una línea (#) y espacios en blanco
        clean_code = re.sub(r'#.*', '', code).strip()
        return len(clean_code) == 0

    def make_hint(
        self,
        code: str,
        exec_result: Dict[str, Any] | None,
        lang: str = "python",
        test_cases: List[Any] | None = None
    ) -> Dict[str, str]:

        exec_result = exec_result or {}
        lang = (lang or "python").lower()

        # --- NUEVA VALIDACIÓN PEDAGÓGICA ---
        if self._is_empty_or_only_comments(code):
            return {
                "pattern_id": "missing_logic",
                "concept": "Code structure",
                "hint": "Veo que has añadido comentarios, pero ¡necesitas escribir la instrucción para imprimir el mensaje!"
            }

        # Si pasa la validación, corre el pipeline normal
        detection = run_detection_pipeline(code, exec_result, test_cases=test_cases or [], lang=lang)

        # Doble check: si el pipeline dice 'correct' pero no hubo salida real
        if detection.pattern_id == "correct" and not exec_result.get("stdout"):
             return {
                "pattern_id": "no_output",
                "concept": "Output",
                "hint": "Tu código es válido, pero no produjo ninguna salida en consola. ¿Olvidaste el print()?"
            }

        return {
            "pattern_id": detection.pattern_id,
            "concept": detection.concept,
            "hint": detection.hint,
        }