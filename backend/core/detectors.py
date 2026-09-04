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
    stdout = str(signals.get("stdout", "")).strip()
    expected = str(signals.get("expected_output", "")).strip()

    if status == "ok":
            # Cuando el ejercicio tiene contrato, la evaluación ya se realizó y
            # es la fuente de verdad. Volver a comparar el stdout completo
            # reintroduciría el rechazo por formato que el evaluador eliminó, y
            # sin casos heredados daría por correcta cualquier ejecución.
            evaluation_status = signals.get("evaluation_status")
            if evaluation_status:
                if evaluation_status == "correct":
                    return DetectionResult(
                        "correct", "", "¡Excelente trabajo! Tu solución es correcta."
                    )
                if evaluation_status == "incorrect":
                    detail = (
                        f" Se esperaba '{expected}' y recibí '{stdout}'."
                        if expected
                        else ""
                    )
                    return DetectionResult(
                        pattern_id="wrong_output",
                        concept="Lógica de salida",
                        hint=(
                            "Tu código no dio error, pero el resultado no coincide "
                            "con el del ejercicio en todos los casos." + detail
                        ),
                    )
                if evaluation_status == "output_inconclusive":
                    return DetectionResult(
                        pattern_id="ambiguous_output",
                        concept="Presentación del resultado",
                        hint=(
                            "Tu programa terminó, pero no fue posible identificar "
                            "cuál de sus salidas es la respuesta. Revisa que el "
                            "resultado quede impreso de forma clara."
                        ),
                    )
                if evaluation_status == "binding_inconclusive":
                    return DetectionResult(
                        pattern_id="ambiguous_input",
                        concept="Datos de entrada",
                        hint=(
                            "No fue posible reconocer los datos que usa tu programa. "
                            "Revisa que pida o defina la misma cantidad de datos que "
                            "plantea el ejercicio."
                        ),
                    )

            # VALIDACIÓN RIGUROSA (camino heredado, sin contrato publicado):
            if expected and stdout != expected:
                return DetectionResult(
                    pattern_id="wrong_output",
                    concept="Lógica de salida",
                    hint=f"Tu código no dio error, pero no imprimió lo esperado. Se esperaba '{expected}' y recibí '{stdout}'."
                )
            # Si el código está vacío (solo comentarios) el stdout será ""
            if not stdout and expected:
                return DetectionResult(
                    pattern_id="no_output",
                    concept="Salida vacía",
                    hint="¡Tu código corre, pero no produce ninguna salida! Asegúrate de usar print()."
                )

            return DetectionResult("correct", "", "¡Excelente trabajo! Tu solución es correcta.")

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
