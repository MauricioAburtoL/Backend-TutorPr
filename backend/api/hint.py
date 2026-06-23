# backend/api/hint.py
import re
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional, Tuple

# Rutas modulares
from ..infra.db import get_db
from ..core.services.TutoringService import TutoringService
from ..core.services.gemini_orchestrator import get_or_fetch
from ..core.services.AnalyticsService import AnalyticsService
from ..infra.storage_sqlite import StorageSQLite
from ..schemas import HintIn, HintOut
from ..core.models import Event, Exercise, TestCase
from ..adapters.python.detectors_py import analyze_syntax

router = APIRouter()
rule_service = TutoringService()

# Regex para extraer linea y tipo de error del stderr de Python
_PY_ERR_LINE = re.compile(r'File "[^"]*", line (\d+)')
_PY_ERR_TYPE = re.compile(r'^(\w+Error):', re.MULTILINE)


def _extract_real_errors(stderr: str) -> List[Dict[str, Any]]:
    """
    Extrae errores reales del stderr de Python con lineas exactas.
    Python nunca se equivoca en sus propios numeros de linea.
    """
    if not stderr:
        return []

    lines = _PY_ERR_LINE.findall(stderr)
    err_type_match = _PY_ERR_TYPE.search(stderr)
    err_type = err_type_match.group(1) if err_type_match else "Error"

    # Clasificar: SyntaxError → "syntax", todo lo demas → "logic"
    kind = "syntax" if "SyntaxError" in err_type or "IndentationError" in err_type else "logic"

    # Extraer la descripcion del error (ultima linea del traceback)
    desc_match = re.search(r'(\w+Error: .+)$', stderr.strip())
    desc = desc_match.group(1) if desc_match else err_type

    errors = []
    seen = set()
    for line_str in lines:
        line_num = int(line_str)
        if line_num not in seen:
            seen.add(line_num)
            errors.append({"line": line_num, "type": kind, "desc": desc})

    return errors


def _merge_all_errors(
    gemini_errors: List[Dict[str, Any]],
    real_errors: List[Dict[str, Any]],
    static_errors: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Merge de 3 fuentes de errores:
    1. real_errors (stderr) — lineas exactas de runtime
    2. static_errors (compilador) — multiples errores de sintaxis
    3. gemini_errors — descripciones pedagogicas + errores logicos

    Prioridad: stderr > static > Gemini para lineas.
    Gemini aporta descripciones pedagogicas y errores logicos unicos.
    """
    # 1. Combinar stderr + static (ambos son Python puro)
    python_errors: Dict[int, Dict[str, Any]] = {}
    for err in real_errors:
        python_errors[err["line"]] = err
    for err in static_errors:
        if err["line"] not in python_errors:
            python_errors[err["line"]] = err

    # 2. Indexar errores de Gemini por linea para buscar descripciones pedagogicas
    gemini_by_line: Dict[int, Dict[str, Any]] = {}
    for g_err in gemini_errors:
        g_line = g_err.get("line", 0)
        if g_line > 0:
            gemini_by_line[g_line] = g_err

    # 3. Para cada error de Python, usar descripcion de Gemini si la tiene (mas pedagogica)
    merged = []
    for line_num in sorted(python_errors.keys()):
        py_err = python_errors[line_num]
        gemini_match = gemini_by_line.get(line_num)
        if gemini_match and gemini_match.get("desc"):
            merged.append({
                "line": py_err["line"],
                "type": py_err["type"],
                "desc": gemini_match["desc"],
            })
        else:
            merged.append(py_err)

    # 4. Agregar errores logicos de Gemini que no estan en lineas ya cubiertas
    covered_lines = {e["line"] for e in merged}
    for g_err in gemini_errors:
        g_line = g_err.get("line", 0)
        if g_line not in covered_lines and g_err.get("type") == "logic":
            merged.append(g_err)

    return sorted(merged, key=lambda e: e["line"])


@router.post("/hint", response_model=HintOut)
def hint(body: HintIn, db: Session = Depends(get_db)):
    exec_data = body.execResult or {}

    # 1. Si la solucion ya es correcta, short-circuit
    if exec_data.get("status") == "ok" and exec_data.get("is_correct") is True:
        return HintOut(
            hint="Tu solucion ya es correcta! No necesitas mas pistas.",
            pattern_id="correct",
            concept="completado",
            source="cache",
            has_more_hints=False,
            detected_errors=[],
        )

    # 2. Obtener contexto real del ejercicio y test cases desde la BD
    exercise = db.query(Exercise).filter(Exercise.id == body.exerciseId).first()
    exercise_context = f"{exercise.title}: {exercise.description}" if exercise else f"Exercise {body.exerciseId}"
    test_cases = db.query(TestCase).filter(TestCase.exercise_id == body.exerciseId).all()

    # 3. Analisis estatico ANTES de Gemini (detecta multiples errores de sintaxis)
    static_errors = analyze_syntax(body.code)

    # 3b. Contexto del estudiante (perfil) para personalizar la pista.
    #     Solo hechos directos; "" para usuario nuevo (degradacion elegante).
    try:
        analytics = AnalyticsService(StorageSQLite(db))
        student_context = analytics.get_prompt_context(body.userId, body.exerciseId)
    except Exception as e:
        print(f"Error construyendo contexto del estudiante: {e}")
        student_context = ""

    # 4. Intentar obtener respuesta de Gemini (cache o nueva llamada)
    try:
        entry = get_or_fetch(
            user_id=body.userId,
            exercise_id=body.exerciseId,
            code=body.code,
            language=(body.lang or "python").lower(),
            context=exercise_context,
            static_errors=static_errors,
            student_context=student_context,
        )

        # 3. Solo caer al fallback si Gemini tuvo un fallo de sistema real
        #    (no cuando status="error" indica que el codigo del alumno tiene errores)
        is_system_failure = (
            entry.response.status == "error"
            and entry.response.pedagogicalFeedback.startswith("System Error:")
            and not entry.response.technicalHints
        )
        if is_system_failure:
            raise ValueError("Gemini system failure")

        # 4. Entrega progresiva de pistas
        hint_text, has_more = entry.next_hint()

        # 5. Serializar detected_errors de Gemini
        gemini_errors = []
        for err in entry.response.detectedErrors:
            if hasattr(err, "model_dump"):
                gemini_errors.append(err.model_dump())
            elif hasattr(err, "dict"):
                gemini_errors.append(err.dict())
            else:
                gemini_errors.append({"line": err.line, "type": err.type, "desc": err.desc})

        # 5b. Extraer errores reales del stderr y combinar las 3 fuentes
        real_errors = _extract_real_errors(exec_data.get("stderr", ""))
        errors_list = _merge_all_errors(gemini_errors, real_errors, static_errors)

        # 6. Telemetria
        try:
            ev = Event(
                user_id=body.userId,
                session_id=body.sessionId,
                exercise_id=body.exerciseId,
                event="FeedbackShown",
                payload={
                    "attempt_id": body.attemptId,
                    "pattern_id": "gemini_progressive",
                    "hint": hint_text,
                    "source": "gemini",
                    "hint_index": entry.hint_index,
                }
            )
            db.add(ev)
            db.commit()
        except Exception:
            db.rollback()

        return HintOut(
            hint=hint_text,
            pattern_id="gemini_progressive",
            concept="AI-assisted",
            source="gemini",
            has_more_hints=has_more,
            detected_errors=errors_list,
        )

    except Exception:
        # 7. FALLBACK: pistas basadas en reglas (sistema original)
        d = rule_service.make_hint(body.code, exec_data, lang=(body.lang or "python").lower(), test_cases=test_cases)

        # Aun sin Gemini, el analisis estatico + stderr dan lineas con error
        real_errors = _extract_real_errors(exec_data.get("stderr", ""))
        fallback_errors = _merge_all_errors([], real_errors, static_errors)

        # Telemetria del fallback
        try:
            ev = Event(
                user_id=body.userId,
                session_id=body.sessionId,
                exercise_id=body.exerciseId,
                event="FeedbackShown",
                payload={
                    "attempt_id": body.attemptId,
                    "pattern_id": d.get("pattern_id", "unknown"),
                    "hint": d.get("hint", ""),
                    "source": "rules",
                }
            )
            db.add(ev)
            db.commit()
        except Exception:
            db.rollback()

        return HintOut(
            hint=d.get("hint", ""),
            pattern_id=d.get("pattern_id", "unknown"),
            concept=d.get("concept", ""),
            source="rules",
            has_more_hints=False,
            detected_errors=fallback_errors,
        )
