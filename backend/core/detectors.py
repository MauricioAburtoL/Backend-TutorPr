# backend/core/detectors.py
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any, Dict

# Puedes especializar por lenguaje si lo necesitas
PY_BUILTINS = {
    "range", "print", "len", "list", "int", "float", "str",
    "bool", "enumerate", "sum", "min", "max"
}

@dataclass
class DetectionResult:
    pattern_id: str
    concept: str
    hint: str

def _py_detect_from_signals(signals: Dict[str, Any]) -> DetectionResult:
    """Detecciones para Python basadas en stderr/status."""
    stderr = signals.get("stderr", "") or ""
    status = signals.get("status", "ok")

    if status == "ok":
        return DetectionResult("correct", "", "Tu solución es correcta.")

    if status == "error":
        # NameError -> distinguir builtin, typo y nombre inexistente
        m = re.search(r"NameError:\s*name\s+'([^']+)'", stderr)
        if m:
            name = m.group(1)
            if name in PY_BUILTINS:
                return DetectionResult(
                    pattern_id="missing_builtin",
                    concept="entorno",
                    hint="El entorno bloqueó funciones básicas como 'range'; "
                         "habilítalas o ejecuta en un entorno completo."
                )
            return DetectionResult(
                pattern_id="name_not_defined",
                concept="identificador",
                hint="El nombre no existe en este alcance; corrige su ortografía "
                     "o declara la variable antes de usarla."
            )

        if "SyntaxError" in stderr:
            return DetectionResult(
                "syntax_error", "estructura",
                "Corrige la estructura; falta o sobra un símbolo de cierre o separador."
            )

        if "IndexError" in stderr:
            return DetectionResult(
                "index_oob", "índices y límites",
                "El índice excede límites; revisa rango y condición final."
            )

        if "TypeError" in stderr:
            return DetectionResult(
                "type_error", "tipos y operaciones",
                "El tipo no coincide con la operación; ajusta conversión o firma."
            )

    # Fallback
    return DetectionResult(
        "unknown", "revisión localizada",
        "Localiza la condición o índice cambiado y prueba un caso límite."
    )

def detect_from_signals(signals: Dict[str, Any], lang: str = "python") -> DetectionResult:
    """Punto único de entrada. Selecciona detector por lenguaje."""
    lang = (lang or "python").lower()
    if lang == "python":
        return _py_detect_from_signals(signals)
    # Hooks para otros lenguajes (Java/C):
    # if lang == "java": return _java_detect_from_signals(signals)
    # if lang in ("c", "cpp"): return _c_detect_from_signals(signals)
    return _py_detect_from_signals(signals)
