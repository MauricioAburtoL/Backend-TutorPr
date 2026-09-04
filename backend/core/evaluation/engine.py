"""Orquestación del evaluador flexible con compatibilidad opt-in por contrato."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List

from pydantic import ValidationError

from ..services.ExecutionService import run_code_sandboxed
from .binding import (
    candidate_mappings,
    code_for_literal_case,
    count_input_calls,
    find_literal_candidates,
    observable_variables,
    resolve_function_target,
    serialize_stdin,
    stdin_value_count,
)
from .contracts import ExerciseContractDefinition, VerificationCase
from .expression import OracleConfigurationError, evaluate_expression
from .output import (
    ParsedOutput,
    any_candidate_matches,
    extract_captured_output,
    extract_output,
    values_match,
)


@dataclass
class CaseRun:
    number: int
    case: VerificationCase
    result: Dict[str, Any]
    parsed: ParsedOutput
    expected: Any
    passed: bool


# Un fallo de ejecución no siempre es responsabilidad del estudiante: quedarse
# sin datos o pedir más de los autorizados describe la forma de la entrada, no
# un error de lógica (`FR-BIND-007`).
_ERROR_STATUS = {
    "SyntaxError": "syntax_error",
    "IndentationError": "syntax_error",
    "TabError": "syntax_error",
    "TimeoutError": "timeout",
    "EOFError": "binding_inconclusive",
    "InputLimitExceeded": "binding_inconclusive",
}

_STATUS_MESSAGE = {
    "syntax_error": "El código contiene un error de sintaxis.",
    "timeout": "La ejecución superó el tiempo permitido.",
    "runtime_error": "El programa produjo un error durante la evaluación.",
    "binding_inconclusive": (
        "El programa esperaba una cantidad de datos distinta de la que "
        "define el ejercicio, así que no fue posible completar la evaluación."
    ),
    "output_inconclusive": (
        "El programa terminó, pero no fue posible identificar un resultado "
        "compatible con el ejercicio."
    ),
    "incorrect": (
        "El programa se ejecutó, pero el resultado no coincide en todos los casos."
    ),
    "correct": "Todos los casos obligatorios pasaron.",
}

_ERROR_MESSAGE = {
    "OutputLimitExceeded": (
        "El programa generó más texto del permitido para este ejercicio; "
        "revisa si hay una impresión dentro de un ciclo que no termina."
    ),
    "EOFError": (
        "El programa pidió más datos de los que define el ejercicio, así que no "
        "fue posible completar la evaluación."
    ),
    "InputLimitExceeded": (
        "El programa solicitó más datos de los permitidos para este ejercicio."
    ),
}


def _empty_runtime_result() -> Dict[str, Any]:
    return {
        "status": "ok",
        "stdout": "",
        "stderr": "",
        "error_type": None,
        "runtime_ms": 0,
        "events": [],
    }


def _sandbox(code: str, evaluation, input_data: str | None = None) -> Dict[str, Any]:
    """Ejecuta en el proceso aislado aplicando los límites del contrato."""
    return run_code_sandboxed(
        code,
        input_data=input_data,
        timeout_seconds=evaluation.limits.execution_timeout_ms / 1000,
        max_output_chars=evaluation.limits.max_output_characters,
        max_input_requests=evaluation.limits.max_input_requests,
    )


def _free_run(code: str, evaluation) -> Dict[str, Any]:
    """Ejecuta el programa tal como fue escrito para poblar la consola.

    Cumple `FR-RUN-001`: pulsar Ejecutar siempre debe mostrar lo que hace el
    programa, incluso cuando la evaluación no pueda completarse.
    """
    result = dict(_sandbox(code, evaluation))
    result.pop("events", None)
    return result


def _configuration_failure(message: str, contract_version: int | None = None):
    return {
        "result": _empty_runtime_result(),
        "evaluation_status": "configuration_error",
        "evaluation_message": "El ejercicio no pudo evaluarse por un error de configuración.",
        "is_correct": False,
        "failed_case": None,
        "test_results": [],
        "contract_version": contract_version,
        "binding_source": None,
        "validation_scope": "none",
        "internal_reason": message,
    }


def _inconclusive(
    status: str,
    message: str,
    contract: ExerciseContractDefinition,
    *,
    code: str | None = None,
    result: Dict[str, Any] | None = None,
    reason: str | None = None,
):
    if result is None:
        if code is None:
            result = _empty_runtime_result()
        else:
            result = _free_run(code, contract.evaluation)
            # Si la ejecución libre revela un fallo real del programa —un ciclo
            # sin fin o una excepción— ese es el desenlace informativo, no la
            # imposibilidad de enlazar entradas (`AC-09`).
            if result.get("status") != "ok":
                error_type = result.get("error_type")
                observed = _runtime_status(error_type)
                if observed != "binding_inconclusive":
                    status = observed
                    message = _ERROR_MESSAGE.get(
                        error_type or "",
                        _STATUS_MESSAGE.get(observed, message),
                    )
    return {
        "result": result,
        "evaluation_status": status,
        "evaluation_message": message,
        "is_correct": False,
        "failed_case": None,
        "test_results": [],
        "contract_version": contract.contract_version,
        "binding_source": None,
        "validation_scope": "none",
        "internal_reason": reason,
    }


def _expected_for_case(evaluation, case: VerificationCase) -> Any:
    if evaluation.oracle.kind == "expression_tree":
        return evaluate_expression(evaluation.oracle.expression, case.inputs)
    if evaluation.oracle.kind == "expected_cases":
        return case.expected
    raise OracleConfigurationError(
        "El oráculo scenario está reservado para la siguiente etapa de implementación"
    )


def _resolve_case_outcome(
    parsed: ParsedOutput,
    expected: Any,
    observation,
) -> tuple[ParsedOutput, bool]:
    """Decide el desenlace de un caso ya ejecutado.

    Cuando el candidato seleccionado no coincide pero otro sí lo hacía, el
    resultado es ambiguo y no incorrecto (`FR-OUT-006`): un mensaje de cierre no
    debe convertir una solución correcta en un fallo de lógica.
    """
    if parsed.status != "parsed":
        return parsed, False
    if values_match(parsed.value, expected, observation):
        return parsed, True
    if parsed.candidates > 1 and any_candidate_matches(parsed, expected, observation):
        return (
            ParsedOutput(
                status="output_inconclusive",
                candidates=parsed.candidates,
                values=parsed.values,
            ),
            False,
        )
    return parsed, False


def _build_run(
    result: Dict[str, Any],
    parsed: ParsedOutput,
    evaluation,
    case: VerificationCase,
    number: int,
) -> CaseRun:
    expected = _expected_for_case(evaluation, case)
    if result.get("status") != "ok":
        return CaseRun(number, case, result, ParsedOutput(status="not_executed"), expected, False)
    parsed, passed = _resolve_case_outcome(parsed, expected, evaluation.observation)
    return CaseRun(number, case, result, parsed, expected, passed)


def _run_case(
    code: str,
    evaluation,
    case: VerificationCase,
    number: int,
    *,
    input_data: str | None = None,
) -> CaseRun:
    result = _sandbox(code, evaluation, input_data=input_data)
    parsed = (
        extract_output(result.get("events", []), evaluation.observation)
        if result.get("status") == "ok"
        else ParsedOutput(status="not_executed")
    )
    return _build_run(result, parsed, evaluation, case, number)


def _run_function_case(
    code: str,
    evaluation,
    case: VerificationCase,
    number: int,
    target_name: str,
) -> CaseRun:
    arguments = ", ".join(
        repr(case.inputs[slot.id]) for slot in evaluation.inputs.slots
    )
    harnessed_code = (
        f"{code.rstrip()}\n\n"
        f"__tutorats_capture__({target_name}({arguments}))\n"
    )
    result = _sandbox(harnessed_code, evaluation)
    parsed = (
        extract_captured_output(result.get("events", []), evaluation.observation)
        if result.get("status") == "ok"
        else ParsedOutput(status="not_executed")
    )
    return _build_run(result, parsed, evaluation, case, number)


def _runtime_status(error_type: str | None) -> str:
    return _ERROR_STATUS.get(error_type or "", "runtime_error")


def _consumed_values(result: Dict[str, Any]) -> int:
    return sum(
        1
        for event in result.get("events", [])
        if event.get("event") == "input_value"
    )


def _aggregate(
    runs: List[CaseRun],
    contract: ExerciseContractDefinition,
    *,
    binding_source: str,
    validation_scope: str = "multiple_cases",
) -> Dict[str, Any]:
    visible = next(
        (run for run in runs if run.case.visibility == "visible"),
        None,
    )
    display_result = dict((visible or runs[0]).result)
    display_result.pop("events", None)
    display_result["runtime_ms"] = sum(
        float(run.result.get("runtime_ms") or 0) for run in runs
    )
    if visible is None:
        display_result["stdout"] = ""
        display_result["stderr"] = ""

    required = [run for run in runs if run.case.required]
    first_error = next(
        (run for run in required if run.result.get("status") != "ok"),
        None,
    )
    first_unparsed = next(
        (run for run in required if run.parsed.status != "parsed"),
        None,
    )
    first_failure = next((run for run in required if not run.passed), None)

    error_type = None
    if first_error is not None:
        error_type = first_error.result.get("error_type")
        evaluation_status = _runtime_status(error_type)
        if first_error.case.visibility == "hidden":
            display_result.update(
                {
                    "status": "error",
                    "stdout": visible.result.get("stdout", "") if visible else "",
                    "stderr": "La ejecución falló en un caso oculto.",
                    "error_type": first_error.result.get("error_type"),
                }
            )
    elif first_unparsed is not None:
        evaluation_status = "output_inconclusive"
    elif first_failure is not None:
        evaluation_status = "incorrect"
    else:
        evaluation_status = "correct"

    evaluation_message = _ERROR_MESSAGE.get(
        error_type or "",
        _STATUS_MESSAGE.get(evaluation_status, _STATUS_MESSAGE["runtime_error"]),
    )

    failed_case = None
    reported_failure = first_error or first_unparsed or first_failure
    if reported_failure is not None:
        failed_case = (
            "Oculto"
            if reported_failure.case.visibility == "hidden"
            else f"Caso visible {reported_failure.number}"
        )

    public_results = [
        {
            "case_number": run.number,
            "is_hidden": run.case.visibility == "hidden",
            "status": run.result.get("status", "error"),
            "evaluation_status": (
                "passed"
                if run.passed
                else (
                    _runtime_status(run.result.get("error_type"))
                    if run.result.get("status") != "ok"
                    else run.parsed.status
                    if run.parsed.status != "parsed"
                    else "failed"
                )
            ),
            "passed": run.passed,
        }
        for run in runs
    ]

    return {
        "result": display_result,
        "evaluation_status": evaluation_status,
        "evaluation_message": evaluation_message,
        "is_correct": evaluation_status == "correct",
        "failed_case": failed_case,
        "test_results": public_results,
        "contract_version": contract.contract_version,
        "binding_source": binding_source,
        "validation_scope": validation_scope,
        "internal_reason": None,
    }


def _mapping_score(runs: List[CaseRun]) -> tuple[int, int, int]:
    passed = sum(1 for run in runs if run.passed)
    parsed = sum(1 for run in runs if run.parsed.status == "parsed")
    executed = sum(1 for run in runs if run.result.get("status") == "ok")
    return passed, parsed, executed


def _all_required_passed(runs: List[CaseRun], total_cases: int) -> bool:
    return len(runs) == total_cases and all(
        run.passed for run in runs if run.case.required
    )


def _stdin_layout_order(evaluation, input_calls: int) -> List[str]:
    layouts = list(evaluation.input_binding.stdin_layouts)
    slot_count = len(evaluation.inputs.slots)
    has_collection = any(
        slot.value_type in {"array", "tuple", "matrix"}
        for slot in evaluation.inputs.slots
    )
    preferred: List[str] = []
    if input_calls == 1 and (slot_count > 1 or has_collection):
        preferred.append("single_line_tokens")
    elif input_calls > 1 and slot_count == 1 and has_collection:
        preferred.append("count_then_values")
    else:
        preferred.append("one_value_per_call")
    ordered: List[str] = []
    for layout in [*preferred, *layouts]:
        if layout in layouts and layout not in ordered:
            ordered.append(layout)
    return ordered


def _run_all_cases(evaluation, prepare) -> List[CaseRun]:
    """Ejecuta los casos deteniéndose en el primer obligatorio que falla."""
    runs: List[CaseRun] = []
    for number, case in enumerate(evaluation.verification.cases, start=1):
        runs.append(prepare(case, number))
        if case.required and not runs[-1].passed:
            break
    return runs


def _evaluate_stdin(code: str, contract: ExerciseContractDefinition, input_calls: int):
    evaluation = contract.evaluation
    total_cases = len(evaluation.verification.cases)
    attempted: List[tuple[str, List[CaseRun]]] = []
    partial_consumption = 0

    for layout in _stdin_layout_order(evaluation, input_calls):
        runs: List[CaseRun] = []
        partial = False
        try:
            for number, case in enumerate(evaluation.verification.cases, start=1):
                run = _run_case(
                    code,
                    evaluation,
                    case,
                    number,
                    input_data=serialize_stdin(
                        evaluation.inputs.slots,
                        case.inputs,
                        layout,
                    ),
                )
                runs.append(run)
                if number == 1 and run.result.get("status") == "ok":
                    consumed = _consumed_values(run.result)
                    expected_values = stdin_value_count(
                        evaluation.inputs.slots,
                        case.inputs,
                        layout,
                    )
                    if consumed < expected_values:
                        # El programa dejó datos sin leer: la entrada no quedó
                        # completamente enlazada (`FR-BIND-006`).
                        partial = True
                        partial_consumption = max(partial_consumption, consumed)
                        break
                if case.required and not run.passed:
                    break
        except ValueError:
            continue

        attempted.append((layout, runs))
        if not partial and _all_required_passed(runs, total_cases):
            return _aggregate(runs, contract, binding_source=f"stdin:{layout}")

    if partial_consumption and "literal_assignment" in evaluation.input_binding.accepted_sources:
        hybrid = _evaluate_hybrid(code, contract, partial_consumption)
        if hybrid is not None:
            return hybrid

    if not attempted:
        return _inconclusive(
            "binding_inconclusive",
            "No fue posible adaptar las entradas al formato solicitado por el programa.",
            contract,
            code=code,
            reason="stdin_layout_inconclusive",
        )

    if partial_consumption:
        return _inconclusive(
            "binding_inconclusive",
            "El programa no utilizó todos los datos del ejercicio, así que no fue "
            "posible comprobar el resultado.",
            contract,
            result=_free_run(code, evaluation),
            reason="partial_input_binding",
        )

    layout, best_runs = max(attempted, key=lambda item: _mapping_score(item[1]))
    return _aggregate(best_runs, contract, binding_source=f"stdin:{layout}")


def _evaluate_hybrid(
    code: str,
    contract: ExerciseContractDefinition,
    consumed: int,
):
    """Enlaza por consola los datos leídos y por literales los restantes.

    Cubre la forma mixta —un dato solicitado al usuario y otro fijado en el
    código— que antes se evaluaba como lógica incorrecta (`FR-BIND-007`).
    """
    evaluation = contract.evaluation
    slots = evaluation.inputs.slots
    if not 0 < consumed < len(slots):
        return None

    stdin_slots = slots[:consumed]
    literal_slots = slots[consumed:]
    candidates = find_literal_candidates(code, restrict_to=observable_variables(code))
    if not candidates or len(candidates) > evaluation.input_binding.max_literal_candidates:
        return None

    mappings = candidate_mappings(
        literal_slots,
        candidates,
        maximum=evaluation.input_binding.max_literal_mappings,
    )
    total_cases = len(evaluation.verification.cases)
    deadline = time.monotonic() + evaluation.input_binding.max_binding_seconds

    for mapping in mappings:
        if time.monotonic() > deadline:
            return None
        runs = _run_all_cases(
            evaluation,
            lambda case, number, mapping=mapping: _run_case(
                code_for_literal_case(code, mapping, case.inputs),
                evaluation,
                case,
                number,
                input_data=serialize_stdin(
                    stdin_slots,
                    case.inputs,
                    "one_value_per_call",
                ),
            ),
        )
        if _all_required_passed(runs, total_cases):
            outcome = _aggregate(
                runs,
                contract,
                binding_source="hybrid:stdin+literal_assignment",
            )
            outcome["binding_candidates"] = len(candidates)
            return outcome
    return None


def _evaluate_function(code: str, contract: ExerciseContractDefinition):
    evaluation = contract.evaluation
    target_name, reason = resolve_function_target(
        code,
        evaluation.target.name_preference,
        evaluation.target.parameter_count,
    )
    if target_name is None:
        expected_name = evaluation.target.name_preference or "la función del ejercicio"
        messages = {
            "no_function_defined": (
                f"Todavía no se encontró ninguna función; el ejercicio espera "
                f"`{expected_name}`."
            ),
            "no_compatible_function": (
                f"No se encontró una función `{expected_name}` que reciba "
                f"{evaluation.target.parameter_count} datos."
            ),
            "ambiguous_function_target": (
                f"Hay varias funciones posibles y ninguna se llama `{expected_name}`, "
                "así que no fue posible saber cuál evaluar."
            ),
        }
        return _inconclusive(
            "binding_inconclusive",
            messages.get(reason, messages["no_compatible_function"]),
            contract,
            code=code,
            reason=reason,
        )

    runs = _run_all_cases(
        evaluation,
        lambda case, number: _run_function_case(
            code,
            evaluation,
            case,
            number,
            target_name,
        ),
    )
    return _aggregate(runs, contract, binding_source=f"function_arguments:{target_name}")


def _evaluate_literals(code: str, contract: ExerciseContractDefinition):
    evaluation = contract.evaluation
    # El corte de dependencias descarta los literales que solo participan en
    # mensajes, y con ello reduce las combinaciones antes de permutarlas
    # (`FR-BIND-009`).
    candidates = find_literal_candidates(code, restrict_to=observable_variables(code))
    if not candidates:
        return _inconclusive(
            "binding_inconclusive",
            "No fue posible identificar valores de entrada en el programa.",
            contract,
            code=code,
            reason="no_literal_candidates",
        )
    if len(candidates) > evaluation.input_binding.max_literal_candidates:
        return _inconclusive(
            "binding_inconclusive",
            "Existen demasiados valores posibles para identificar las entradas con seguridad.",
            contract,
            code=code,
            reason="literal_candidate_limit",
        )

    mappings = candidate_mappings(
        evaluation.inputs.slots,
        candidates,
        maximum=evaluation.input_binding.max_literal_mappings,
    )
    if not mappings:
        return _inconclusive(
            "binding_inconclusive",
            "No fue posible asociar los valores del programa con las entradas del ejercicio.",
            contract,
            code=code,
            reason="no_safe_literal_mapping",
        )

    total_cases = len(evaluation.verification.cases)
    deadline = time.monotonic() + evaluation.input_binding.max_binding_seconds
    attempted: List[List[CaseRun]] = []

    for mapping in mappings:
        if attempted and time.monotonic() > deadline:
            # Agotado el presupuesto, el resultado es inconcluso y nunca un
            # veredicto emitido a medias (`FR-BIND-008`).
            return _inconclusive(
                "binding_inconclusive",
                "No fue posible identificar las entradas del programa dentro del "
                "tiempo disponible.",
                contract,
                result=_free_run(code, evaluation),
                reason="binding_budget_exhausted",
            )
        runs = _run_all_cases(
            evaluation,
            lambda case, number, mapping=mapping: _run_case(
                code_for_literal_case(code, mapping, case.inputs),
                evaluation,
                case,
                number,
            ),
        )
        attempted.append(runs)
        if _all_required_passed(runs, total_cases):
            outcome = _aggregate(
                runs,
                contract,
                binding_source="literal_assignment:auto",
            )
            outcome["binding_candidates"] = len(candidates)
            outcome["binding_mappings_evaluated"] = len(attempted)
            return outcome

    best_runs = max(attempted, key=_mapping_score)
    outcome = _aggregate(
        best_runs,
        contract,
        binding_source="literal_assignment:auto",
    )
    outcome["binding_candidates"] = len(candidates)
    outcome["binding_mappings_evaluated"] = len(attempted)
    return outcome


def evaluate_flexible_exercise(
    code: str,
    raw_contract: Dict[str, Any],
) -> Dict[str, Any]:
    """Evalúa un contrato publicado sin afectar el camino heredado."""
    try:
        contract = ExerciseContractDefinition.model_validate(raw_contract)
    except ValidationError as exc:
        return _configuration_failure(str(exc))

    evaluation = contract.evaluation
    if evaluation.kind == "class_method":
        return _configuration_failure(
            f"La modalidad {evaluation.kind} todavía no está activa",
            contract.contract_version,
        )
    if evaluation.oracle.kind not in {"expression_tree", "expected_cases"}:
        return _configuration_failure(
            f"El oráculo {evaluation.oracle.kind} todavía no está activo",
            contract.contract_version,
        )

    try:
        if evaluation.kind == "function":
            return _evaluate_function(code, contract)
        input_calls = count_input_calls(code)
        if input_calls and "stdin" in evaluation.input_binding.accepted_sources:
            return _evaluate_stdin(code, contract, input_calls)
        if "literal_assignment" in evaluation.input_binding.accepted_sources:
            return _evaluate_literals(code, contract)
        return _inconclusive(
            "binding_inconclusive",
            "La forma de entrada del programa no está habilitada para este ejercicio.",
            contract,
            code=code,
            reason="unsupported_input_source",
        )
    except SyntaxError:
        result = _free_run(code, evaluation)
        return {
            "result": result,
            "evaluation_status": "syntax_error",
            "evaluation_message": _STATUS_MESSAGE["syntax_error"],
            "is_correct": False,
            "failed_case": None,
            "test_results": [],
            "contract_version": contract.contract_version,
            "binding_source": None,
            "validation_scope": "none",
            "internal_reason": "syntax_error_before_binding",
        }
    except (
        OracleConfigurationError,
        ArithmeticError,
        TypeError,
        ValueError,
        KeyError,
        IndexError,
    ) as exc:
        return _configuration_failure(str(exc), contract.contract_version)
