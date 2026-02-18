# backend/core/pipeline.py
import re
from typing import Any, Dict, List
from .detectors import DetectionResult, detect_from_signals

def run_detection_pipeline(
    code: str, 
    exec_result: Dict[str, Any], 
    test_cases: List[Any], 
    lang: str = "python"
) -> DetectionResult:
    """
    Pipeline de detección. Aquí puedes:
      - Normalizar señales,
      - Encadenar varios detectores,
      - Fusionar con reglas adicionales o RAG.
    """
    
    # 1. Limpieza de comentarios para verificar si hay código real
    stripped_code = re.sub(r'#.*', '', code).strip()

    # 2. Heurística: Si no hay código real, devolvemos un resultado preventivo
    if not stripped_code:
        return DetectionResult(
            pattern_id="missing_logic",
            concept="Estructura básica",
            hint="¡Buen comienzo con los comentarios! Pero aún falta la instrucción para imprimir tu mensaje en consola."
        )

    # 3. Extraer la salida esperada de los Test Cases (de la DB)
    # Buscamos el caso de prueba que no sea oculto para usarlo como referencia de feedback
    primary_test = next((tc for tc in test_cases if not getattr(tc, 'is_hidden', False)), None)
    expected = getattr(primary_test, 'expected_output', "") if primary_test else ""

    # 4. Preparación de señales enriquecidas con datos de la DB
    signals = {
        "status": exec_result.get("status", "ok"),
        "stderr": exec_result.get("stderr", "") or "",
        "stdout": exec_result.get("stdout", "") or "",
        "expected_output": expected, # 👈 Inyectamos la "verdad" de la base de datos
        "code": code,
        "clean_code": stripped_code 
    }
    
    return detect_from_signals(signals, lang=lang)