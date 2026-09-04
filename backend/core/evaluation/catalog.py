"""Contratos y contenido publicados inicialmente por el prototipo."""

from ..eva02_tasks import (
    EVA02_EXERCISES,
    EVA02_TOPIC,
    TASK_1_INITIAL_CODE,
    TASK_2_INITIAL_CODE,
    TASK_3_INITIAL_CODE,
)

TRIANGLE_AREA_STARTER_CODE = (
    "# Calcula el área de un triángulo\n"
    "# Lee la base y la altura, luego imprime el área\n"
    'base = float(input("Dame la base: "))\n'
    'altura = float(input("Dame la altura: "))\n'
    "# Tu código aquí\n"
)

TRIANGLE_AREA_CONTRACT = {
    "schema_version": 1,
    "exercise_id": "e-sec-1",
    "contract_version": 1,
    "evaluation": {
        "kind": "script",
        "inputs": {
            "slots": [
                {"id": "base", "type": "number"},
                {"id": "altura", "type": "number"},
            ]
        },
        "input_binding": {
            "mode": "auto",
            "accepted_sources": ["stdin", "literal_assignment"],
            "stdin_layouts": ["one_value_per_call", "single_line_tokens"],
            "max_literal_candidates": 8,
            "max_literal_mappings": 64,
            "ambiguity_policy": "inconclusive",
        },
        "observation": {
            "source": "stdout_events",
            "selection": "last_parseable",
            "type": "number",
            "allow_extra_output": True,
            "absolute_tolerance": 1e-9,
            "relative_tolerance": 1e-9,
            "ambiguity_policy": "inconclusive",
        },
        "oracle": {
            "kind": "expression_tree",
            "expression": {
                "operation": "divide",
                "arguments": [
                    {
                        "operation": "multiply",
                        "arguments": [
                            {"input": "base"},
                            {"input": "altura"},
                        ],
                    },
                    {"constant": 2},
                ],
            },
        },
        "verification": {
            "cases": [
                {
                    "inputs": {"base": 10, "altura": 5},
                    "visibility": "visible",
                    "required": True,
                },
                {
                    "inputs": {"base": 6, "altura": 4},
                    "visibility": "hidden",
                    "required": True,
                },
                {
                    "inputs": {"base": 3, "altura": 7},
                    "visibility": "hidden",
                    "required": True,
                },
            ]
        },
        "limits": {
            "execution_timeout_ms": 3000,
            "max_output_characters": 100000,
            "max_input_requests": 20,
        },
    },
}


MAX_N_STARTER_CODE = (
    "# Encuentra el número mayor de una cantidad variable de datos\n"
    'numeros = list(map(float, input("Dame los números separados por espacios: ").split()))\n'
    "# Tu código aquí\n"
)

PALINDROME_STARTER_CODE = (
    "# Determina si un texto es palíndromo\n"
    'texto = input("Dame una palabra o frase: ")\n'
    "# Tu código aquí\n"
)

REVERSE_LIST_STARTER_CODE = (
    "# Invierte el orden de los elementos de una lista\n"
    'numeros = list(map(int, input("Dame los números separados por espacios: ").split()))\n'
    "# Tu código aquí\n"
)

FLEXIBLE_PILOT_TOPIC = {
    "id": "evaluacion-flexible",
    "title": "Ejercicios de evaluación flexible",
    "description": (
        "Ejercicios de control para validar distintas formas de entrada, "
        "nombres libres y resultados tipados."
    ),
    "icon": "🧩",
    "category": "Evaluación",
    "total_exercises": 3,
    "tags": ["Entradas", "Cadenas", "Listas", "Evaluación flexible"],
    "estimated_time": "30 min",
}

FLEXIBLE_PILOT_EXERCISES = [
    {
        "id": "flex-max-n",
        "topic_id": FLEXIBLE_PILOT_TOPIC["id"],
        "order": 1,
        "title": "Mayor de N números",
        "description": (
            "Lee una cantidad variable de números e imprime el mayor. "
            "Puedes organizar los datos y nombrar tus variables libremente."
        ),
        "difficulty": "Fácil",
        "base_code": MAX_N_STARTER_CODE,
    },
    {
        "id": "flex-palindrome",
        "topic_id": FLEXIBLE_PILOT_TOPIC["id"],
        "order": 2,
        "title": "Detectar un palíndromo",
        "description": (
            "Indica si una palabra o frase se lee igual en ambos sentidos. "
            "La comparación ignora espacios y diferencias entre mayúsculas y minúsculas."
        ),
        "difficulty": "Fácil",
        "base_code": PALINDROME_STARTER_CODE,
    },
    {
        "id": "flex-reverse-list",
        "topic_id": FLEXIBLE_PILOT_TOPIC["id"],
        "order": 3,
        "title": "Invertir una lista",
        "description": (
            "Lee una lista de números e imprime otra lista con los mismos "
            "elementos en orden inverso."
        ),
        "difficulty": "Fácil",
        "base_code": REVERSE_LIST_STARTER_CODE,
    },
]


EVA02_TASK_1_CONTRACT = {
    "schema_version": 1,
    "exercise_id": "eva02-t1",
    "contract_version": 1,
    "evaluation": {
        "kind": "function",
        "target": {
            "name_preference": "mayor_de_tres",
            "parameter_count": 3,
            "return_type": "integer",
        },
        "inputs": {
            "slots": [
                {"id": "primero", "type": "integer"},
                {"id": "segundo", "type": "integer"},
                {"id": "tercero", "type": "integer"},
            ]
        },
        "observation": {
            "source": "return_value",
            "selection": "return_value",
            "type": "integer",
        },
        "oracle": {"kind": "expected_cases"},
        "verification": {
            "cases": [
                {"inputs": {"primero": 1, "segundo": 1, "tercero": 2}, "visibility": "visible", "expected": 2},
                {"inputs": {"primero": 1, "segundo": 2, "tercero": 3}, "visibility": "visible", "expected": 3},
                {"inputs": {"primero": 3, "segundo": 2, "tercero": 1}, "visibility": "visible", "expected": 3},
                {"inputs": {"primero": 2, "segundo": 2, "tercero": 1}, "visibility": "visible", "expected": 2},
                {"inputs": {"primero": 3, "segundo": 3, "tercero": 3}, "visibility": "hidden", "expected": 3},
                {"inputs": {"primero": -1, "segundo": -2, "tercero": -3}, "visibility": "hidden", "expected": -1},
                {"inputs": {"primero": 1, "segundo": 3, "tercero": 3}, "visibility": "hidden", "expected": 3},
            ]
        },
        "limits": {"execution_timeout_ms": 3000},
    },
}

EVA02_TASK_2_CONTRACT = {
    "schema_version": 1,
    "exercise_id": "eva02-t2",
    "contract_version": 1,
    "evaluation": {
        "kind": "function",
        "target": {
            "name_preference": "sumar_pares_impares",
            "parameter_count": 1,
            "return_type": "tuple",
        },
        "inputs": {"slots": [{"id": "limite", "type": "integer"}]},
        "observation": {
            "source": "return_value",
            "selection": "return_value",
            "type": "tuple",
        },
        "oracle": {"kind": "expected_cases"},
        "verification": {
            "cases": [
                {"inputs": {"limite": 5}, "visibility": "visible", "expected": [6, 9]},
                {"inputs": {"limite": 10}, "visibility": "visible", "expected": [30, 25]},
                {"inputs": {"limite": 0}, "visibility": "hidden", "expected": [0, 0]},
                {"inputs": {"limite": 1}, "visibility": "hidden", "expected": [0, 1]},
                {"inputs": {"limite": 2}, "visibility": "hidden", "expected": [2, 1]},
            ]
        },
        "limits": {"execution_timeout_ms": 3000},
    },
}

EVA02_TASK_3_CONTRACT = {
    "schema_version": 1,
    "exercise_id": "eva02-t3",
    "contract_version": 1,
    "evaluation": {
        "kind": "function",
        "target": {
            "name_preference": "esta_ordenada_ascendente",
            "parameter_count": 1,
            "return_type": "boolean",
        },
        "inputs": {
            "slots": [
                {"id": "datos", "type": "array", "item_type": "integer", "max_items": 100}
            ]
        },
        "observation": {
            "source": "return_value",
            "selection": "return_value",
            "type": "boolean",
        },
        "oracle": {"kind": "expected_cases"},
        "verification": {
            "cases": [
                {"inputs": {"datos": [1, 2, 3, 4]}, "visibility": "visible", "expected": True},
                {"inputs": {"datos": [1, 2, 5, 4]}, "visibility": "visible", "expected": False},
                {"inputs": {"datos": [3, 2, 4]}, "visibility": "visible", "expected": False},
                {"inputs": {"datos": [1, 2, 3, 0]}, "visibility": "hidden", "expected": False},
                {"inputs": {"datos": [1, 1, 2, 2]}, "visibility": "hidden", "expected": True},
                {"inputs": {"datos": [7]}, "visibility": "hidden", "expected": True},
                {"inputs": {"datos": []}, "visibility": "hidden", "expected": True},
            ]
        },
        "limits": {"execution_timeout_ms": 3000},
    },
}

MAX_N_CONTRACT = {
    "schema_version": 1,
    "exercise_id": "flex-max-n",
    "contract_version": 1,
    "evaluation": {
        "kind": "script",
        "inputs": {
            "slots": [
                {"id": "numeros", "type": "array", "item_type": "number", "min_items": 1, "max_items": 100}
            ]
        },
        "input_binding": {
            "accepted_sources": ["stdin", "literal_assignment"],
            "stdin_layouts": [
                "single_line_tokens",
                "count_then_values",
                "one_value_per_call",
                "values_then_blank",
            ],
        },
        "observation": {
            "source": "stdout_events",
            "selection": "last_parseable",
            "type": "number",
        },
        "oracle": {
            "kind": "expression_tree",
            "expression": {"operation": "maximum", "arguments": [{"input": "numeros"}]},
        },
        "verification": {
            "cases": [
                {"inputs": {"numeros": [5, 0, 1]}, "visibility": "visible"},
                {"inputs": {"numeros": [-4, -2, -9]}, "visibility": "hidden"},
                {"inputs": {"numeros": [7]}, "visibility": "hidden"},
                {"inputs": {"numeros": [1.5, 8.2, 3]}, "visibility": "hidden"},
            ]
        },
        "limits": {"execution_timeout_ms": 3000},
    },
}

PALINDROME_CONTRACT = {
    "schema_version": 1,
    "exercise_id": "flex-palindrome",
    "contract_version": 1,
    "evaluation": {
        "kind": "script",
        "inputs": {"slots": [{"id": "texto", "type": "string"}]},
        "input_binding": {
            "accepted_sources": ["stdin", "literal_assignment"],
            "stdin_layouts": ["one_value_per_call"],
        },
        "observation": {
            "source": "stdout_events",
            "selection": "last_parseable",
            "type": "boolean",
            # Perfil declarado: «Es un palíndromo» afirma y «No es un palíndromo»
            # niega. Sin las palabras del ejercicio no se interpreta nada.
            "boolean_profile": "negation_aware",
            "boolean_keywords": ["palindromo", "palíndromo", "capicua"],
        },
        "oracle": {
            "kind": "expression_tree",
            "expression": {
                "operation": "equals",
                "arguments": [
                    {"operation": "normalize", "arguments": [{"input": "texto"}]},
                    {"operation": "reverse", "arguments": [
                        {"operation": "normalize", "arguments": [{"input": "texto"}]}
                    ]},
                ],
            },
        },
        "verification": {
            "cases": [
                {"inputs": {"texto": "radar"}, "visibility": "visible"},
                {"inputs": {"texto": "casa"}, "visibility": "hidden"},
                {"inputs": {"texto": "Reconocer"}, "visibility": "hidden"},
                {"inputs": {"texto": "anita lava la tina"}, "visibility": "hidden"},
            ]
        },
        "limits": {"execution_timeout_ms": 3000},
    },
}

REVERSE_LIST_CONTRACT = {
    "schema_version": 1,
    "exercise_id": "flex-reverse-list",
    "contract_version": 1,
    "evaluation": {
        "kind": "script",
        "inputs": {
            "slots": [
                {"id": "numeros", "type": "array", "item_type": "integer", "max_items": 100}
            ]
        },
        "input_binding": {
            "accepted_sources": ["stdin", "literal_assignment"],
            "stdin_layouts": [
                "single_line_tokens",
                "count_then_values",
                "one_value_per_call",
                "values_then_blank",
            ],
        },
        "observation": {
            "source": "stdout_events",
            "selection": "last_parseable",
            "type": "array",
            "item_type": "integer",
            # Formas de presentación admitidas: la lista impresa, los elementos
            # uno por línea y los elementos separados en una sola línea.
            "collection_formats": ["literal", "per_line", "joined_line"],
        },
        "oracle": {
            "kind": "expression_tree",
            "expression": {"operation": "reverse", "arguments": [{"input": "numeros"}]},
        },
        "verification": {
            # La lista vacía no forma parte de los casos obligatorios: bajo el
            # formato «un elemento por línea» una solución correcta no imprime
            # nada, y el resultado no sería distinguible de una ausencia.
            "cases": [
                {"inputs": {"numeros": [1, 2, 3, 4]}, "visibility": "visible"},
                {"inputs": {"numeros": [7, 3]}, "visibility": "hidden"},
                {"inputs": {"numeros": [2, 2, 9, 1]}, "visibility": "hidden"},
                {"inputs": {"numeros": [-1, 0, 5]}, "visibility": "hidden"},
            ]
        },
        "limits": {"execution_timeout_ms": 3000},
    },
}


PUBLISHED_EXERCISE_CONTRACTS = [
    TRIANGLE_AREA_CONTRACT,
    EVA02_TASK_1_CONTRACT,
    EVA02_TASK_2_CONTRACT,
    EVA02_TASK_3_CONTRACT,
    MAX_N_CONTRACT,
    PALINDROME_CONTRACT,
    REVERSE_LIST_CONTRACT,
]

PUBLISHED_EXERCISE_STARTERS = {
    "e-sec-1": TRIANGLE_AREA_STARTER_CODE,
    "eva02-t1": TASK_1_INITIAL_CODE,
    "eva02-t2": TASK_2_INITIAL_CODE,
    "eva02-t3": TASK_3_INITIAL_CODE,
    "flex-max-n": MAX_N_STARTER_CODE,
    "flex-palindrome": PALINDROME_STARTER_CODE,
    "flex-reverse-list": REVERSE_LIST_STARTER_CODE,
}

PUBLISHED_EXERCISE_TOPICS = [EVA02_TOPIC, FLEXIBLE_PILOT_TOPIC]

PUBLISHED_EXERCISES = [*EVA02_EXERCISES, *FLEXIBLE_PILOT_EXERCISES]
