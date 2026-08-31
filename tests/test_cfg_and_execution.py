import time
import unittest

from backend.core.cfg import build_cfg_any
from backend.core.eva02_tasks import (
    EVA02_EXERCISES,
    EVA02_SOLUTIONS,
    EVA02_TEST_CASES,
)
from backend.core.services.ExecutionService import compose_test_code, run_code_sandboxed
from backend.core.services.TutoringService import TutoringService


class CfgFunctionBodyTests(unittest.TestCase):
    def test_function_body_control_flow_is_included(self):
        code = """\
def evaluar(x):
    if x > 0:
        for i in range(x):
            print(i)
        return x
    return 0

print(evaluar(2))
"""
        cfg = build_cfg_any("python", code)
        labels_by_id = {node["id"]: node["label"] for node in cfg["nodes"]}

        self.assertIn("if x > 0", labels_by_id.values())
        self.assertIn("for i in range(x)", labels_by_id.values())
        self.assertIn("return x", labels_by_id.values())
        self.assertIn("return 0", labels_by_id.values())

        function_id = next(
            node_id
            for node_id, label in labels_by_id.items()
            if label == "def evaluar(x)"
        )
        if_id = next(
            node_id
            for node_id, label in labels_by_id.items()
            if label == "if x > 0"
        )
        loop_id = next(
            node_id
            for node_id, label in labels_by_id.items()
            if label == "for i in range(x)"
        )
        zero_return_id = next(
            node_id
            for node_id, label in labels_by_id.items()
            if label == "return 0"
        )
        self.assertIn((function_id, if_id), cfg["edges"])
        self.assertIn((if_id, loop_id), cfg["edges"])
        self.assertIn((if_id, zero_return_id), cfg["edges"])
        self.assertNotIn((if_id, if_id), cfg["edges"])


class SandboxedExecutionTests(unittest.TestCase):
    def test_input_is_passed_to_worker(self):
        result = run_code_sandboxed(
            "n = int(input())\nprint(n * 2)",
            "4\n",
        )

        self.assertEqual("ok", result["status"])
        self.assertEqual("8", result["stdout"].strip())

    def test_infinite_loop_is_terminated(self):
        started = time.perf_counter()
        result = run_code_sandboxed(
            "while True:\n    pass",
            timeout_seconds=0.5,
        )
        elapsed = time.perf_counter() - started

        self.assertEqual("error", result["status"])
        self.assertEqual("TimeoutError", result["error_type"])
        self.assertLess(elapsed, 2)

    def test_excessive_output_is_terminated(self):
        result = run_code_sandboxed("print('x' * 100001)")

        self.assertEqual("error", result["status"])
        self.assertEqual("OutputLimitExceeded", result["error_type"])
        self.assertEqual(100000, len(result["stdout"]))


class Eva02IntegrationTests(unittest.TestCase):
    def test_each_initial_code_fails_and_each_solution_passes(self):
        exercises = {exercise["id"]: exercise for exercise in EVA02_EXERCISES}

        for exercise_id, solution in EVA02_SOLUTIONS.items():
            cases = [
                case
                for case in EVA02_TEST_CASES
                if case["exercise_id"] == exercise_id
            ]
            initial = exercises[exercise_id]["base_code"]

            initial_results = [self._case_passes(initial, case) for case in cases]
            solution_results = [self._case_passes(solution, case) for case in cases]

            self.assertFalse(
                all(initial_results),
                f"El código inicial de {exercise_id} no debe aprobar todos los casos",
            )
            self.assertTrue(
                all(solution_results),
                f"La solución patrón de {exercise_id} debe aprobar todos los casos",
            )

    def test_each_task_has_visible_and_hidden_cases(self):
        for exercise in EVA02_EXERCISES:
            cases = [
                case
                for case in EVA02_TEST_CASES
                if case["exercise_id"] == exercise["id"]
            ]
            self.assertTrue(any(not case["is_hidden"] for case in cases))
            self.assertTrue(any(case["is_hidden"] for case in cases))

    def test_rule_fallback_matches_each_prepared_defect(self):
        expected_patterns = {
            "eva02-t1": "igualdad",
            "eva02-t2": "acumulado",
            "eva02-t3": "último par",
        }
        service = TutoringService()

        for exercise in EVA02_EXERCISES:
            hint = service.make_hint(
                exercise["base_code"],
                {"status": "ok", "stdout": "salida incorrecta"},
                exercise_id=exercise["id"],
            )
            self.assertIn(
                expected_patterns[exercise["id"]],
                hint["hint"].lower(),
            )

    def test_visible_output_cannot_bypass_hidden_cases(self):
        visible_only_programs = {
            "eva02-t1": "print(2)\nprint(3)\nprint(3)\nprint(2)",
            "eva02-t2": "print((6, 9))\nprint((30, 25))",
            "eva02-t3": "print(True)\nprint(False)\nprint(False)",
        }

        for exercise_id, code in visible_only_programs.items():
            cases = [
                case
                for case in EVA02_TEST_CASES
                if case["exercise_id"] == exercise_id
            ]
            visible = next(case for case in cases if not case["is_hidden"])
            hidden = [case for case in cases if case["is_hidden"]]

            self.assertTrue(self._case_passes(code, visible))
            self.assertFalse(all(self._case_passes(code, case) for case in hidden))

    @staticmethod
    def _case_passes(code, case):
        result = run_code_sandboxed(
            compose_test_code(code, case.get("test_code")),
            input_data=case.get("input_data"),
        )
        return (
            result["status"] == "ok"
            and result["stdout"].strip() == case["expected_output"].strip()
        )


if __name__ == "__main__":
    unittest.main()
