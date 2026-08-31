"""Definición canónica de las tres tareas usadas en el instrumento EVA-02."""

EVA02_TOPIC = {
    "id": "evaluacion-eva02",
    "title": "Actividades de evaluación",
    "description": (
        "Tres actividades breves de depuración para la aplicación de EVA-02."
    ),
    "icon": "🧪",
    "category": "Evaluación",
    "total_exercises": 3,
    "tags": ["Condicionales", "Ciclos", "Listas", "Depuración"],
    "estimated_time": "30 min",
}


TASK_1_INITIAL_CODE = """\
def mayor_de_tres(a, b, c):
    if a > b and a > c:
        return a
    elif b > a and b > c:
        return b
    else:
        return c


print(mayor_de_tres(1, 1, 2))
print(mayor_de_tres(1, 2, 3))
print(mayor_de_tres(3, 2, 1))
print(mayor_de_tres(2, 2, 1))
"""

TASK_1_SOLUTION_CODE = """\
def mayor_de_tres(a, b, c):
    if a >= b and a >= c:
        return a
    elif b >= a and b >= c:
        return b
    return c


print(mayor_de_tres(1, 1, 2))
print(mayor_de_tres(1, 2, 3))
print(mayor_de_tres(3, 2, 1))
print(mayor_de_tres(2, 2, 1))
"""

TASK_2_INITIAL_CODE = """\
def sumar_pares_impares(limite):
    contador = 1
    suma_pares = 0
    suma_impares = 0

    while contador <= limite:
        if contador % 2 == 0:
            suma_pares = contador
        else:
            suma_impares = contador

        contador = contador + 1

    return suma_pares, suma_impares


print(sumar_pares_impares(5))
print(sumar_pares_impares(10))
"""

TASK_2_SOLUTION_CODE = """\
def sumar_pares_impares(limite):
    contador = 1
    suma_pares = 0
    suma_impares = 0

    while contador <= limite:
        if contador % 2 == 0:
            suma_pares = suma_pares + contador
        else:
            suma_impares = suma_impares + contador
        contador = contador + 1

    return suma_pares, suma_impares


print(sumar_pares_impares(5))
print(sumar_pares_impares(10))
"""

TASK_3_INITIAL_CODE = """\
def esta_ordenada_ascendente(datos):
    for i in range(len(datos) - 2):
        if datos[i] > datos[i + 1]:
            return False

    return True


print(esta_ordenada_ascendente([1, 2, 3, 4]))
print(esta_ordenada_ascendente([1, 2, 5, 4]))
print(esta_ordenada_ascendente([3, 2, 4]))
"""

TASK_3_SOLUTION_CODE = """\
def esta_ordenada_ascendente(datos):
    for i in range(len(datos) - 1):
        if datos[i] > datos[i + 1]:
            return False
    return True


print(esta_ordenada_ascendente([1, 2, 3, 4]))
print(esta_ordenada_ascendente([1, 2, 5, 4]))
print(esta_ordenada_ascendente([3, 2, 4]))
"""


EVA02_EXERCISES = [
    {
        "id": "eva02-t1",
        "topic_id": EVA02_TOPIC["id"],
        "order": 1,
        "title": "Determinar el número mayor",
        "description": (
            "Corrige el programa sin cambiar las cuatro llamadas de prueba. "
            "Las salidas esperadas, en orden, son: 2, 3, 3 y 2."
        ),
        "difficulty": "Fácil",
        "base_code": TASK_1_INITIAL_CODE,
    },
    {
        "id": "eva02-t2",
        "topic_id": EVA02_TOPIC["id"],
        "order": 2,
        "title": "Sumar números pares e impares",
        "description": (
            "Corrige los acumuladores sin cambiar las llamadas de prueba. "
            "Las salidas esperadas son (6, 9) y (30, 25)."
        ),
        "difficulty": "Medio",
        "base_code": TASK_2_INITIAL_CODE,
    },
    {
        "id": "eva02-t3",
        "topic_id": EVA02_TOPIC["id"],
        "order": 3,
        "title": "Verificar el orden de una lista",
        "description": (
            "Corrige el recorrido sin cambiar las listas de prueba. "
            "Las salidas esperadas, en orden, son: True, False y False."
        ),
        "difficulty": "Medio",
        "base_code": TASK_3_INITIAL_CODE,
    },
]


EVA02_TEST_CASES = [
    {
        "exercise_id": "eva02-t1",
        "input_data": None,
        "test_code": None,
        "expected_output": "2\n3\n3\n2",
        "is_hidden": False,
    },
    {
        "exercise_id": "eva02-t1",
        "input_data": None,
        "test_code": "print(mayor_de_tres(3, 3, 3))",
        "expected_output": "2\n3\n3\n2\n3",
        "is_hidden": True,
    },
    {
        "exercise_id": "eva02-t1",
        "input_data": None,
        "test_code": "print(mayor_de_tres(-1, -2, -3))",
        "expected_output": "2\n3\n3\n2\n-1",
        "is_hidden": True,
    },
    {
        "exercise_id": "eva02-t1",
        "input_data": None,
        "test_code": "print(mayor_de_tres(1, 3, 3))",
        "expected_output": "2\n3\n3\n2\n3",
        "is_hidden": True,
    },
    {
        "exercise_id": "eva02-t2",
        "input_data": None,
        "test_code": None,
        "expected_output": "(6, 9)\n(30, 25)",
        "is_hidden": False,
    },
    {
        "exercise_id": "eva02-t2",
        "input_data": None,
        "test_code": "print(sumar_pares_impares(0))",
        "expected_output": "(6, 9)\n(30, 25)\n(0, 0)",
        "is_hidden": True,
    },
    {
        "exercise_id": "eva02-t2",
        "input_data": None,
        "test_code": "print(sumar_pares_impares(1))",
        "expected_output": "(6, 9)\n(30, 25)\n(0, 1)",
        "is_hidden": True,
    },
    {
        "exercise_id": "eva02-t2",
        "input_data": None,
        "test_code": "print(sumar_pares_impares(2))",
        "expected_output": "(6, 9)\n(30, 25)\n(2, 1)",
        "is_hidden": True,
    },
    {
        "exercise_id": "eva02-t3",
        "input_data": None,
        "test_code": None,
        "expected_output": "True\nFalse\nFalse",
        "is_hidden": False,
    },
    {
        "exercise_id": "eva02-t3",
        "input_data": None,
        "test_code": "print(esta_ordenada_ascendente([1, 2, 3, 0]))",
        "expected_output": "True\nFalse\nFalse\nFalse",
        "is_hidden": True,
    },
    {
        "exercise_id": "eva02-t3",
        "input_data": None,
        "test_code": "print(esta_ordenada_ascendente([1, 1, 2, 2]))",
        "expected_output": "True\nFalse\nFalse\nTrue",
        "is_hidden": True,
    },
    {
        "exercise_id": "eva02-t3",
        "input_data": None,
        "test_code": "print(esta_ordenada_ascendente([7]))",
        "expected_output": "True\nFalse\nFalse\nTrue",
        "is_hidden": True,
    },
    {
        "exercise_id": "eva02-t3",
        "input_data": None,
        "test_code": "print(esta_ordenada_ascendente([]))",
        "expected_output": "True\nFalse\nFalse\nTrue",
        "is_hidden": True,
    },
]


EVA02_SOLUTIONS = {
    "eva02-t1": TASK_1_SOLUTION_CODE,
    "eva02-t2": TASK_2_SOLUTION_CODE,
    "eva02-t3": TASK_3_SOLUTION_CODE,
}
