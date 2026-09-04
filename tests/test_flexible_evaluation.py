"""Regresión del motor de evaluación flexible (`SPEC-EVAL-01`, sección 24).

Cada prueba corresponde a una forma de resolver observada en programación
introductoria o a un defecto registrado durante la primera verificación. La
suite es la condición de cierre del `Incremento V1`.
"""

import copy
import json
import time
import unittest

from pydantic import ValidationError

from backend.core.evaluation import evaluate_flexible_exercise
from backend.core.pipeline import run_detection_pipeline
from backend.core.evaluation.contracts import ExerciseContractDefinition
from backend.core.evaluation.catalog import (
    EVA02_TASK_1_CONTRACT,
    EVA02_TASK_3_CONTRACT,
    MAX_N_CONTRACT,
    PALINDROME_CONTRACT,
    PUBLISHED_EXERCISE_CONTRACTS,
    REVERSE_LIST_CONTRACT,
    TRIANGLE_AREA_CONTRACT,
)


def evaluate(code, contract):
    return evaluate_flexible_exercise(code.strip() + "\n", contract)


def status(code, contract):
    return evaluate(code, contract)["evaluation_status"]


class ContractValidation(unittest.TestCase):
    def test_every_published_contract_validates(self):
        for contract in PUBLISHED_EXERCISE_CONTRACTS:
            with self.subTest(contract["exercise_id"]):
                ExerciseContractDefinition.model_validate(contract)

    def test_an_unknown_oracle_operation_is_rejected_before_publishing(self):
        broken = copy.deepcopy(TRIANGLE_AREA_CONTRACT)
        broken["evaluation"]["oracle"]["expression"] = {
            "operation": "promedio",
            "arguments": [{"input": "base"}],
        }
        with self.assertRaises(ValidationError):
            ExerciseContractDefinition.model_validate(broken)

    def test_a_case_with_an_unknown_input_id_is_rejected(self):
        broken = copy.deepcopy(TRIANGLE_AREA_CONTRACT)
        broken["evaluation"]["verification"]["cases"][0]["inputs"] = {
            "base": 10,
            "alto": 5,
        }
        with self.assertRaises(ValidationError):
            ExerciseContractDefinition.model_validate(broken)


class RunningAlwaysProducesConsole(unittest.TestCase):
    """`FR-RUN-001`: pulsar Ejecutar siempre muestra lo que hace el programa."""

    def test_an_exploratory_print_is_executed_and_shown(self):
        outcome = evaluate('print("Hola, voy empezando")', TRIANGLE_AREA_CONTRACT)
        self.assertEqual(outcome["evaluation_status"], "binding_inconclusive")
        self.assertIn("Hola, voy empezando", outcome["result"]["stdout"])

    def test_an_endless_loop_without_inputs_is_reported_as_timeout(self):
        contract = copy.deepcopy(TRIANGLE_AREA_CONTRACT)
        contract["evaluation"]["limits"]["execution_timeout_ms"] = 1000
        outcome = evaluate("while True:\n    pass", contract)
        self.assertEqual(outcome["evaluation_status"], "timeout")

    def test_the_declared_output_limit_reaches_the_sandbox(self):
        contract = copy.deepcopy(TRIANGLE_AREA_CONTRACT)
        contract["evaluation"]["limits"]["max_output_characters"] = 100
        outcome = evaluate(
            'b = float(input())\n'
            'h = float(input())\n'
            'for i in range(2000):\n'
            '    print("relleno", i)\n'
            'print(b * h / 2)',
            contract,
        )
        self.assertLessEqual(len(outcome["result"]["stdout"]), 100)


class InputBinding(unittest.TestCase):
    def test_free_variable_names_do_not_change_the_verdict(self):
        self.assertEqual(
            status(
                'print("Hola, calcularemos el area")\n'
                'base_elegida = float(input("Dame la base: "))\n'
                'altura_elegida = float(input("Dame la altura: "))\n'
                'print("El area es:", base_elegida * altura_elegida / 2)',
                TRIANGLE_AREA_CONTRACT,
            ),
            "correct",
        )

    def test_literal_assignments_are_bound_without_markers(self):
        self.assertEqual(
            status("b = 5\nh = 10\nprint(b * h / 2)", TRIANGLE_AREA_CONTRACT),
            "correct",
        )

    def test_a_constant_is_not_confused_with_an_input(self):
        self.assertEqual(
            status(
                "x = 5\ny = 10\ndivisor = 2\nprint(x * y / divisor)",
                TRIANGLE_AREA_CONTRACT,
            ),
            "correct",
        )

    def test_a_mixed_console_and_literal_program_is_bound(self):
        """`FR-BIND-007`: antes se evaluaba como lógica incorrecta."""
        outcome = evaluate(
            'base = float(input("Dame la base: "))\naltura = 10\nprint(base * altura / 2)',
            TRIANGLE_AREA_CONTRACT,
        )
        self.assertEqual(outcome["evaluation_status"], "correct")
        self.assertEqual(
            outcome["binding_source"],
            "hybrid:stdin+literal_assignment",
        )

    def test_a_sentinel_loop_is_supported(self):
        """`FR-BIND-006`: antes terminaba en EOFError atribuido al estudiante."""
        self.assertEqual(
            status(
                'numeros = []\n'
                'dato = input("Numero: ")\n'
                'while dato != "":\n'
                '    numeros.append(float(dato))\n'
                '    dato = input("Numero: ")\n'
                'print(max(numeros))',
                MAX_N_CONTRACT,
            ),
            "correct",
        )

    def test_a_counted_loop_selects_the_count_then_values_layout(self):
        outcome = evaluate(
            'n = int(input("Cuantos: "))\n'
            'numeros = []\n'
            'for i in range(n):\n'
            '    numeros.append(float(input("Numero: ")))\n'
            'print(max(numeros))',
            MAX_N_CONTRACT,
        )
        self.assertEqual(outcome["evaluation_status"], "correct")
        self.assertEqual(outcome["binding_source"], "stdin:count_then_values")

    def test_presentation_literals_do_not_multiply_the_search(self):
        """`FR-BIND-009`: el corte de dependencias excluye los mensajes."""
        noise = "\n".join(f'mensaje{i} = "texto {i}"' for i in range(8))
        started = time.monotonic()
        outcome = evaluate(
            f'{noise}\nb = 5\nh = 10\nprint(b * h / 2)',
            TRIANGLE_AREA_CONTRACT,
        )
        self.assertEqual(outcome["evaluation_status"], "correct")
        self.assertLess(time.monotonic() - started, 3.0)

    def test_the_binding_budget_is_respected(self):
        """`FR-BIND-008`: nunca una espera indefinida."""
        started = time.monotonic()
        evaluate(
            "\n".join(f"v{i} = {i + 1}" for i in range(8))
            + "\nprint(v0 * v1 * v2 * v3 * v4 * v5 * v6 * v7)",
            TRIANGLE_AREA_CONTRACT,
        )
        self.assertLess(time.monotonic() - started, 8.0)


class OutputInterpretation(unittest.TestCase):
    def test_a_trailing_message_with_a_number_does_not_produce_incorrect(self):
        """`FR-OUT-006`: el desenlace es ambiguo, no un fallo de lógica."""
        self.assertEqual(
            status(
                'b = float(input())\n'
                'h = float(input())\n'
                'print("Area:", b * h / 2)\n'
                'print("Programa terminado. Version 2")',
                TRIANGLE_AREA_CONTRACT,
            ),
            "output_inconclusive",
        )

    def test_a_wrong_solution_is_still_incorrect(self):
        self.assertEqual(
            status(
                "b = float(input())\nh = float(input())\nprint(b * h)",
                TRIANGLE_AREA_CONTRACT,
            ),
            "incorrect",
        )

    def test_an_affirmative_sentence_is_read_as_true(self):
        """`FR-OUT-008`: perfil declarado con las palabras del ejercicio."""
        self.assertEqual(
            status(
                'texto = input("Palabra: ")\n'
                'limpio = texto.lower().replace(" ", "")\n'
                'if limpio == limpio[::-1]:\n'
                '    print("Es un palindromo")\n'
                'else:\n'
                '    print("No es un palindromo")',
                PALINDROME_CONTRACT,
            ),
            "correct",
        )

    def test_a_closing_message_is_not_read_as_a_boolean_answer(self):
        self.assertEqual(
            status(
                'print("Bienvenido al detector")\n'
                'texto = input("Palabra: ")\n'
                'limpio = texto.lower().replace(" ", "")\n'
                'print("Si" if limpio == limpio[::-1] else "No")\n'
                'print("Fin del programa")',
                PALINDROME_CONTRACT,
            ),
            "correct",
        )

    def test_a_collection_printed_one_item_per_line_is_recognised(self):
        """`FR-OUT-007`: la salida más frecuente del temario de listas."""
        self.assertEqual(
            status(
                "numeros = list(map(int, input().split()))\n"
                "for x in reversed(numeros):\n"
                "    print(x)",
                REVERSE_LIST_CONTRACT,
            ),
            "correct",
        )

    def test_a_collection_joined_in_one_line_is_recognised(self):
        self.assertEqual(
            status(
                "numeros = list(map(int, input().split()))\n"
                'print(" ".join(str(x) for x in numeros[::-1]))',
                REVERSE_LIST_CONTRACT,
            ),
            "correct",
        )

    def test_a_collection_printed_as_a_literal_is_recognised(self):
        self.assertEqual(
            status(
                "numeros = list(map(int, input().split()))\n"
                'print("La lista invertida es:", numeros[::-1])',
                REVERSE_LIST_CONTRACT,
            ),
            "correct",
        )


class FunctionMode(unittest.TestCase):
    def test_a_correct_function_passes_every_case(self):
        self.assertEqual(
            status(
                "def mayor_de_tres(a, b, c):\n"
                "    if a >= b and a >= c:\n"
                "        return a\n"
                "    elif b >= c:\n"
                "        return b\n"
                "    return c",
                EVA02_TASK_1_CONTRACT,
            ),
            "correct",
        )

    def test_a_renamed_function_is_located_by_arity(self):
        """`FR-FUN-001`: el nombre no determina por sí solo la corrección."""
        outcome = evaluate(
            "def mayor(a, b, c):\n    return max(a, b, c)",
            EVA02_TASK_1_CONTRACT,
        )
        self.assertEqual(outcome["evaluation_status"], "correct")
        self.assertEqual(outcome["binding_source"], "function_arguments:mayor")

    def test_a_missing_function_is_inconclusive_and_not_a_runtime_error(self):
        """`FR-FUN-002`: mensaje accionable en lugar de NameError."""
        outcome = evaluate("x = 5", EVA02_TASK_1_CONTRACT)
        self.assertEqual(outcome["evaluation_status"], "binding_inconclusive")
        self.assertIn("mayor_de_tres", outcome["evaluation_message"])

    def test_printing_instead_of_returning_is_inconclusive(self):
        self.assertEqual(
            status(
                "def mayor_de_tres(a, b, c):\n    print(max(a, b, c))",
                EVA02_TASK_1_CONTRACT,
            ),
            "output_inconclusive",
        )

    def test_a_defective_function_is_rejected(self):
        self.assertEqual(
            status(
                "def esta_ordenada_ascendente(datos):\n    return True",
                EVA02_TASK_3_CONTRACT,
            ),
            "incorrect",
        )


class TeacherAuthoredExercise(unittest.TestCase):
    """Un ejercicio nuevo debe publicarse sin modificar el backend."""

    AVERAGE = {
        "schema_version": 1,
        "exercise_id": "doc-promedio",
        "contract_version": 1,
        "evaluation": {
            "kind": "script",
            "inputs": {
                "slots": [
                    {"id": "n1", "type": "number"},
                    {"id": "n2", "type": "number"},
                    {"id": "n3", "type": "number"},
                ]
            },
            "input_binding": {
                "accepted_sources": ["stdin", "literal_assignment"],
                "stdin_layouts": ["one_value_per_call", "single_line_tokens"],
            },
            "observation": {
                "source": "stdout_events",
                "selection": "last_parseable",
                "type": "number",
            },
            "oracle": {
                "kind": "expression_tree",
                "expression": {
                    "operation": "divide",
                    "arguments": [
                        {
                            "operation": "add",
                            "arguments": [
                                {
                                    "operation": "add",
                                    "arguments": [{"input": "n1"}, {"input": "n2"}],
                                },
                                {"input": "n3"},
                            ],
                        },
                        {"constant": 3},
                    ],
                },
            },
            "verification": {
                "cases": [
                    {"inputs": {"n1": 7, "n2": 8, "n3": 9}, "visibility": "visible"},
                    {"inputs": {"n1": 10, "n2": 10, "n3": 10}, "visibility": "hidden"},
                    {"inputs": {"n1": 4, "n2": 5, "n3": 6}, "visibility": "hidden"},
                ]
            },
            "limits": {"execution_timeout_ms": 3000},
        },
    }

    def test_a_new_exercise_defined_only_as_a_contract_evaluates_students(self):
        self.assertEqual(
            status(
                'print("Calculadora de promedio")\n'
                'a = float(input("Nota 1: "))\n'
                'b = float(input("Nota 2: "))\n'
                'c = float(input("Nota 3: "))\n'
                'print("El promedio es:", (a + b + c) / 3)',
                self.AVERAGE,
            ),
            "correct",
        )

    def test_the_same_exercise_accepts_a_literal_solution(self):
        self.assertEqual(
            status("a = 7\nb = 8\nc = 9\nprint((a + b + c) / 3)", self.AVERAGE),
            "correct",
        )


class HiddenDataIsNotExposed(unittest.TestCase):
    def test_public_results_never_carry_inputs_or_expected_values(self):
        outcome = evaluate(
            "b = float(input())\nh = float(input())\nprint(b * h)",
            TRIANGLE_AREA_CONTRACT,
        )
        allowed = {
            "case_number",
            "is_hidden",
            "status",
            "evaluation_status",
            "passed",
        }
        for entry in outcome["test_results"]:
            self.assertEqual(set(entry) - allowed, set())

    def test_a_hidden_failure_is_reported_without_its_data(self):
        contract = copy.deepcopy(TRIANGLE_AREA_CONTRACT)
        contract["evaluation"]["verification"]["cases"][0]["visibility"] = "hidden"
        outcome = evaluate(
            "b = float(input())\nh = float(input())\nprint(b * h)",
            contract,
        )
        self.assertEqual(outcome["failed_case"], "Oculto")
        self.assertNotIn("10", json.dumps(outcome["test_results"]))


class HintFallbackHonoursTheEvaluation(unittest.TestCase):
    """El respaldo por reglas no debe reevaluar por su cuenta.

    Cuando el ejercicio tiene contrato, el veredicto ya se emitió. Comparar de
    nuevo el `stdout` completo reintroduciría el rechazo por formato, y sin
    casos heredados daría por correcta cualquier ejecución.
    """

    class VisibleCase:
        is_hidden = False
        expected_output = "25.0"

    def test_a_wrong_solution_without_legacy_cases_is_not_praised(self):
        result = run_detection_pipeline(
            "texto = input()\nprint('Si')",
            {"status": "ok", "stdout": "Si", "stderr": "", "evaluation_status": "incorrect"},
            [],
        )
        self.assertEqual(result.pattern_id, "wrong_output")

    def test_a_correct_solution_with_extra_messages_is_not_rejected(self):
        result = run_detection_pipeline(
            'b = float(input())\nprint("El area es:", b)',
            {
                "status": "ok",
                "stdout": "El area es: 25.0",
                "stderr": "",
                "evaluation_status": "correct",
            },
            [self.VisibleCase()],
        )
        self.assertEqual(result.pattern_id, "correct")

    def test_inconclusive_states_get_their_own_guidance(self):
        for evaluation_status, pattern in [
            ("output_inconclusive", "ambiguous_output"),
            ("binding_inconclusive", "ambiguous_input"),
        ]:
            with self.subTest(evaluation_status):
                result = run_detection_pipeline(
                    'print("algo")',
                    {
                        "status": "ok",
                        "stdout": "algo",
                        "stderr": "",
                        "evaluation_status": evaluation_status,
                    },
                    [],
                )
                self.assertEqual(result.pattern_id, pattern)

    def test_the_legacy_path_keeps_comparing_against_its_test_case(self):
        result = run_detection_pipeline(
            "print(50.0)",
            {"status": "ok", "stdout": "50.0", "stderr": ""},
            [self.VisibleCase()],
        )
        self.assertEqual(result.pattern_id, "wrong_output")
        self.assertIn("25.0", result.hint)


if __name__ == "__main__":
    unittest.main()
