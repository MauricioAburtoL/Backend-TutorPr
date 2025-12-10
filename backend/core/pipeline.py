# backend/core/pipeline.py
from __future__ import annotations
from typing import Any, Dict
from .detectors import DetectionResult, detect_from_signals

def run_detection_pipeline(code: str, exec_result: Dict[str, Any], lang: str = "python") -> DetectionResult:
    """
    Pipeline de detección. Aquí puedes:
      - Normalizar señales,
      - Encadenar varios detectores,
      - Fusionar con reglas adicionales o RAG.
    """
    signals = {
        "status": exec_result.get("status", "ok"),
        "stderr": exec_result.get("stderr", "") or "",
        "stdout": exec_result.get("stdout", "") or "",
        "code": code,
    }
    return detect_from_signals(signals, lang=lang)
