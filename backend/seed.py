import json
from backend.infra.db import SessionLocal, engine, Base
from backend.core import models

def seed_data():
    # Crea las tablas si no existen
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # =============================================
        # 1. TEMAS (Topics) — Alineados al syllabus
        # =============================================
        topics_data = [
            {
                "id": "secuencial",
                "title": "Estructura Secuencial",
                "description": "Domina la sintaxis esencial: variables, operaciones aritméticas, entrada/salida y asignación.",
                "icon": "📝",
                "category": "Fundamentos",
                "total_exercises": 6,
                "tags": ["Variables", "Aritmética", "Input/Output", "Asignación"],
                "estimated_time": "1h 30m"
            },
            {
                "id": "selectiva",
                "title": "Estructura Selectiva",
                "description": "Aprende a tomar decisiones lógicas con if/else y condiciones compuestas.",
                "icon": "🔀",
                "category": "Lógica",
                "total_exercises": 5,
                "tags": ["If/Else", "Condiciones", "Operadores Relacionales", "Módulo"],
                "estimated_time": "2h 00m"
            },
            {
                "id": "repetitiva",
                "title": "Estructura Repetitiva",
                "description": "Automatiza tareas con ciclos for y while, contadores y acumuladores.",
                "icon": "🔁",
                "category": "Lógica",
                "total_exercises": 5,
                "tags": ["For", "While", "Contadores", "Acumuladores"],
                "estimated_time": "2h 15m"
            },
            {
                "id": "arreglos",
                "title": "Arreglos y Listas",
                "description": "Trabaja con estructuras de datos lineales: listas, búsqueda e inserción.",
                "icon": "📦",
                "category": "Estructuras",
                "total_exercises": 2,
                "tags": ["Listas", "Búsqueda", "Inserción", "Vectores"],
                "estimated_time": "1h 30m"
            },
            {
                "id": "matrices",
                "title": "Matrices",
                "description": "Maneja arreglos bidimensionales: creación, operaciones y recorridos.",
                "icon": "🔢",
                "category": "Estructuras",
                "total_exercises": 3,
                "tags": ["Matrices 2D", "Suma de Matrices", "Recorridos"],
                "estimated_time": "2h 00m"
            },
            {
                "id": "poo-basica",
                "title": "POO Básica",
                "description": "Crea clases, objetos, constructores y métodos básicos.",
                "icon": "🏗️",
                "category": "POO",
                "total_exercises": 6,
                "tags": ["Clases", "Objetos", "Constructores", "Métodos"],
                "estimated_time": "2h 30m"
            },
            {
                "id": "poo-intermedia",
                "title": "POO Intermedia",
                "description": "Domina encapsulamiento, getters/setters y métodos avanzados.",
                "icon": "🔒",
                "category": "POO",
                "total_exercises": 7,
                "tags": ["Encapsulamiento", "Get/Set", "Atributos Privados"],
                "estimated_time": "3h 00m"
            },
            {
                "id": "arreglos-objetos",
                "title": "Arreglos de Objetos",
                "description": "Combina arreglos con objetos para modelar colecciones complejas.",
                "icon": "📚",
                "category": "Estructuras",
                "total_exercises": 4,
                "tags": ["Arreglos", "Objetos", "Búsqueda", "Colecciones"],
                "estimated_time": "2h 30m"
            },
            {
                "id": "ordenamiento",
                "title": "Ordenamiento",
                "description": "Implementa algoritmos clásicos de ordenamiento: burbuja y selección directa.",
                "icon": "📊",
                "category": "Estructuras",
                "total_exercises": 2,
                "tags": ["Burbuja", "Selección Directa", "Algoritmos"],
                "estimated_time": "1h 30m"
            },
        ]

        # =============================================
        # 2. EJERCICIOS (Exercises)
        # =============================================
        exercises_data = [
            # --- SECUENCIAL ---
            {
                "id": "e-sec-1", "topic_id": "secuencial", "order": 1,
                "title": "Área de un triángulo",
                "description": "Calcular el área de un triángulo dada su base y altura. Usa la fórmula: área = base × altura / 2.",
                "difficulty": "Fácil",
                "base_code": "# Calcula el área de un triángulo\n# Lee la base y la altura, luego imprime el área\nbase = int(input())\naltura = int(input())\n# Tu código aquí\n"
            },
            {
                "id": "e-sec-2", "topic_id": "secuencial", "order": 2,
                "title": "Suma del doble y cubo",
                "description": "Dados dos números, calcular la suma del doble del primero más el cubo del segundo. Ejemplo: con 3 y 2 → (3×2) + (2³) = 6 + 8 = 14.",
                "difficulty": "Fácil",
                "base_code": "# Dados dos números, calcula: (doble del primero) + (cubo del segundo)\na = int(input())\nb = int(input())\n# Tu código aquí\n"
            },
            {
                "id": "e-sec-3", "topic_id": "secuencial", "order": 3,
                "title": "Producto cuadrado y triple",
                "description": "Dados dos números, calcular el producto del cuadrado del primero más el triple del segundo. Ejemplo: con 3 y 4 → (3²) × (4×3) = 9 × 12... Nota: interpreta la operación como (a²) + (3×b).",
                "difficulty": "Fácil",
                "base_code": "# Dados dos números, calcula: (cuadrado del primero) + (triple del segundo)\na = int(input())\nb = int(input())\n# Tu código aquí\n"
            },
            {
                "id": "e-sec-4", "topic_id": "secuencial", "order": 4,
                "title": "Conversión de segundos",
                "description": "Dada una cantidad de segundos, indicar cuántas horas, minutos y segundos la forman. Ejemplo: 3661 → 1 hora, 1 minuto, 1 segundo.",
                "difficulty": "Medio",
                "base_code": "# Convierte una cantidad de segundos a horas, minutos y segundos\nsegundos_total = int(input())\n# Tu código aquí\n# Imprime: horas, minutos, segundos\n"
            },
            {
                "id": "e-sec-5", "topic_id": "secuencial", "order": 5,
                "title": "Intercambio de variables",
                "description": "Intercambiar el valor almacenado en dos variables e imprimir los valores antes y después del intercambio.",
                "difficulty": "Fácil",
                "base_code": "# Intercambia el valor de dos variables\na = int(input())\nb = int(input())\nprint(a, b)\n# Realiza el intercambio aquí\n# Imprime los nuevos valores\n"
            },
            {
                "id": "e-sec-6", "topic_id": "secuencial", "order": 6,
                "title": "Conversión de estatura",
                "description": "Convertir estatura de pies y pulgadas a metros. 1 pie = 12 pulgadas, 1 pulgada = 2.54 cm, 1 m = 100 cm.",
                "difficulty": "Medio",
                "base_code": "# Convierte estatura de pies y pulgadas a metros\npies = int(input())\npulgadas = int(input())\n# Tu código aquí\n"
            },

            # --- SELECTIVA ---
            {
                "id": "e-sel-1", "topic_id": "selectiva", "order": 1,
                "title": "Mayor de tres números",
                "description": "Dados tres números, determinar cuál es el mayor usando condiciones compuestas.",
                "difficulty": "Fácil",
                "base_code": "# Determina el mayor de 3 números\nnum1 = int(input())\nnum2 = int(input())\nnum3 = int(input())\n# Tu código aquí\n"
            },
            {
                "id": "e-sel-2", "topic_id": "selectiva", "order": 2,
                "title": "Par o impar",
                "description": "Dado un número, determinar si es par o impar usando el operador módulo (%).",
                "difficulty": "Fácil",
                "base_code": "# Determina si un número es par o impar\nnum = int(input())\n# Tu código aquí\n"
            },
            {
                "id": "e-sel-3", "topic_id": "selectiva", "order": 3,
                "title": "Múltiplo de 5",
                "description": "Escribir un programa que muestre un mensaje afirmativo si el número introducido es múltiplo de 5.",
                "difficulty": "Fácil",
                "base_code": "# Verifica si un número es múltiplo de 5\nnum = int(input())\n# Tu código aquí\n"
            },
            {
                "id": "e-sel-4", "topic_id": "selectiva", "order": 4,
                "title": "Sueldo con horas extra",
                "description": "Calcular el sueldo semanal de un empleado. Se paga por hora trabajada. Si trabaja más de 40 horas, las horas extra se pagan al doble.",
                "difficulty": "Medio",
                "base_code": "# Calcula sueldo semanal con horas extra\nhoras = int(input())\npago_hora = float(input())\n# Si trabaja > 40 horas, las extra se pagan al doble\n# Tu código aquí\n"
            },
            {
                "id": "e-sel-5", "topic_id": "selectiva", "order": 5,
                "title": "Hora después de un segundo",
                "description": "Dada la hora actual (hrs, min, seg), determinar la hora después de un segundo. Ejemplo: 8:59:59 → 9:00:00.",
                "difficulty": "Medio",
                "base_code": "# Calcula la hora después de un segundo\nhrs = int(input())\nmin = int(input())\nseg = int(input())\n# Tu código aquí\n"
            },

            # --- REPETITIVA ---
            {
                "id": "e-rep-1", "topic_id": "repetitiva", "order": 1,
                "title": "Serie de 1 a n",
                "description": "Imprimir los números del 1 al n usando un ciclo while.",
                "difficulty": "Fácil",
                "base_code": "# Imprime los números del 1 al n\nn = int(input())\n# Tu código aquí\n"
            },
            {
                "id": "e-rep-2", "topic_id": "repetitiva", "order": 2,
                "title": "Suma de pares e impares",
                "description": "Calcular la suma de los números pares y la suma de los números impares del 1 al 200.",
                "difficulty": "Fácil",
                "base_code": "# Calcula la suma de pares y la suma de impares del 1 al 200\n# Tu código aquí\n"
            },
            {
                "id": "e-rep-3", "topic_id": "repetitiva", "order": 3,
                "title": "Suma con for",
                "description": "Dado un número n, calcular la suma de los números del 0 al n usando un ciclo for.",
                "difficulty": "Fácil",
                "base_code": "# Calcula la suma de 0 a n usando for\nn = int(input())\n# Tu código aquí\n"
            },
            {
                "id": "e-rep-4", "topic_id": "repetitiva", "order": 4,
                "title": "Suma de múltiplos de 5",
                "description": "Calcular la suma de los primeros n múltiplos de 5. Ejemplo: n=3 → 5 + 10 + 15 = 30.",
                "difficulty": "Medio",
                "base_code": "# Suma de los primeros n múltiplos de 5\nn = int(input())\n# Tu código aquí\n"
            },
            {
                "id": "e-rep-5", "topic_id": "repetitiva", "order": 5,
                "title": "Promedio de n números",
                "description": "Calcular el promedio de n números dados por el usuario.",
                "difficulty": "Medio",
                "base_code": "# Calcula el promedio de n números\nn = int(input())\n# Lee n números y calcula su promedio\n# Tu código aquí\n"
            },

            # --- ARREGLOS ---
            {
                "id": "e-arr-1", "topic_id": "arreglos", "order": 1,
                "title": "Operaciones con arreglos",
                "description": "Dado un vector de n elementos, crear el arreglo, llenarlo con datos del usuario e imprimir sus elementos.",
                "difficulty": "Fácil",
                "base_code": "# Crea un arreglo de n elementos y muéstralos\nn = int(input())\nvector = [0] * n\n# Lee los datos y luego imprime el arreglo\n# Tu código aquí\n"
            },
            {
                "id": "e-arr-2", "topic_id": "arreglos", "order": 2,
                "title": "Búsqueda e inserción ordenada",
                "description": "Dado un arreglo ordenado, insertar un nuevo elemento en la posición correcta para mantener el orden.",
                "difficulty": "Medio",
                "base_code": "# Inserta un elemento en un arreglo ordenado\nvector = [2, 5, 8, 12, 20]\nnuevo = int(input())\n# Inserta 'nuevo' en la posición correcta\n# Tu código aquí\nprint(vector)\n"
            },

            # --- MATRICES ---
            {
                "id": "e-mat-1", "topic_id": "matrices", "order": 1,
                "title": "Suma de matrices",
                "description": "Crear dos matrices de 3×3 con datos fijos y calcular su suma elemento a elemento.",
                "difficulty": "Medio",
                "base_code": "# Suma de dos matrices 3x3\nmat1 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]\nmat2 = [[9, 8, 7], [6, 5, 4], [3, 2, 1]]\nresultado = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]\n# Calcula la suma y muestra el resultado\n# Tu código aquí\n"
            },
            {
                "id": "e-mat-2", "topic_id": "matrices", "order": 2,
                "title": "Transpuesta de una matriz",
                "description": "Dada una matriz 3×3, calcular y mostrar su transpuesta (intercambiar filas por columnas).",
                "difficulty": "Medio",
                "base_code": "# Transpuesta de una matriz 3x3\nmatriz = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]\ntranspuesta = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]\n# Calcula la transpuesta y muéstrala\n# Tu código aquí\n"
            },
            {
                "id": "e-mat-3", "topic_id": "matrices", "order": 3,
                "title": "Ventas semanales",
                "description": "Dada una matriz de ventas (productos × días), calcular el total de ventas por día y por producto.",
                "difficulty": "Medio",
                "base_code": "# Ventas semanales: 3 productos × 5 días\nventas = [\n    [10, 20, 15, 30, 25],\n    [5, 10, 8, 12, 7],\n    [20, 15, 25, 10, 30]\n]\nproductos = ['Producto A', 'Producto B', 'Producto C']\ndias = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie']\n# Calcula totales por día y por producto\n# Tu código aquí\n"
            },

            # --- POO BASICA ---
            {
                "id": "e-poo1-1", "topic_id": "poo-basica", "order": 1,
                "title": "Clase Perro",
                "description": "Crear una clase Perro con atributos nombre, color y raza. Incluir métodos ladrar(), correr() y saludar().",
                "difficulty": "Fácil",
                "base_code": "# Crea la clase Perro con atributos y métodos\nclass Perro:\n    # Define el constructor y los métodos\n    pass\n\n# Programa principal\nmi_perro = Perro('Max', 'Pinto', 'Schnauzer')\nmi_perro.ladrar()\nmi_perro.correr()\nmi_perro.saludar()\n"
            },
            {
                "id": "e-poo1-2", "topic_id": "poo-basica", "order": 2,
                "title": "Clase Cuadrado",
                "description": "Crear una clase Cuadrado con un atributo lado y métodos para calcular el área y el perímetro.",
                "difficulty": "Fácil",
                "base_code": "# Crea la clase Cuadrado\nclass Cuadrado:\n    # Define constructor, area() y perimetro()\n    pass\n\n# Programa principal\ncuad = Cuadrado(5)\ncuad.area()\ncuad.perimetro()\n"
            },
            {
                "id": "e-poo1-3", "topic_id": "poo-basica", "order": 3,
                "title": "Clase Persona",
                "description": "Crear una clase Persona con atributos nombre y edad, un método saludar() y un método actualizaEdad().",
                "difficulty": "Fácil",
                "base_code": "# Crea la clase Persona\nclass Persona:\n    # Define constructor, saludar() y actualizaEdad()\n    pass\n\n# Programa principal\np1 = Persona('Lorena', 30)\np1.saludar()\np2 = Persona('David', 20)\np2.saludar()\np3 = Persona('Carlos', 15)\np3.saludar()\np3.actualizaEdad()\n"
            },
            {
                "id": "e-poo1-4", "topic_id": "poo-basica", "order": 4,
                "title": "Clase Cuadrado B",
                "description": "Crear una clase Cuadrado que imprima directamente el área y el perímetro desde sus métodos.",
                "difficulty": "Fácil",
                "base_code": "# Clase Cuadrado con métodos que imprimen resultados\nclass Cuadrado:\n    # Define constructor, area() y perimetro()\n    pass\n\nlado = int(input())\ncuad = Cuadrado(lado)\ncuad.area()\ncuad.perimetro()\n"
            },
            {
                "id": "e-poo1-5", "topic_id": "poo-basica", "order": 5,
                "title": "Clase Número de 4 dígitos",
                "description": "Crear una clase Numero que valide si un número tiene 4 dígitos, extraiga el dígito de las unidades y sume todos sus dígitos.",
                "difficulty": "Medio",
                "base_code": "# Clase para manipular números de 4 dígitos\nclass Numero:\n    # Constructor, validar(), digitoUnidad(), sumarDigitos()\n    pass\n\nnum = int(input())\nn = Numero(num)\nn.validar()\nn.digitoUnidad()\nn.sumarDigitos()\n"
            },
            {
                "id": "e-poo1-6", "topic_id": "poo-basica", "order": 6,
                "title": "Clase Persona - Extraer nombre",
                "description": "Crear una clase Persona con nombre completo y un método para extraer el segundo nombre.",
                "difficulty": "Fácil",
                "base_code": "# Clase Persona que extrae el segundo nombre\nclass Persona:\n    # Constructor y método segundoNombre()\n    pass\n\np1 = Persona('Juan Carlos')\nprint('Segundo nombre ', p1.segundoNombre())\np2 = Persona('Maria')\nprint('Segundo nombre', p2.segundoNombre())\n"
            },

            # --- POO INTERMEDIA ---
            {
                "id": "e-poo2-1", "topic_id": "poo-intermedia", "order": 1,
                "title": "Getters y Setters",
                "description": "Crear una clase Cuadrado con atributo privado __lado y métodos setLado(), getLado(), area() y perimetro().",
                "difficulty": "Medio",
                "base_code": "# Clase Cuadrado con getters y setters\nclass Cuadrado:\n    # Atributo privado __lado\n    # Métodos: setLado, getLado, area, perimetro\n    pass\n\ncuad = Cuadrado(5)\ncuad.area()\ncuad.perimetro()\ncuad.setLado(3)\ncuad.area()\ncuad.perimetro()\n"
            },
            {
                "id": "e-poo2-2", "topic_id": "poo-intermedia", "order": 2,
                "title": "Cuadrado con encapsulamiento",
                "description": "Implementar una clase Cuadrado con atributo privado, demostrar que no se puede acceder directamente al atributo privado.",
                "difficulty": "Medio",
                "base_code": "# Cuadrado con atributo privado\nclass Cuadrado:\n    # __lado como atributo privado\n    # setLado, getLado, area, perimetro\n    pass\n\nlado = int(input())\ncuad = Cuadrado(lado)\ncuad.area()\ncuad.perimetro()\n"
            },
            {
                "id": "e-poo2-3", "topic_id": "poo-intermedia", "order": 3,
                "title": "Clase Hora",
                "description": "Crear una clase Hora (hr, min, seg) con métodos para mostrar la hora formateada, calcular la hora después de un segundo y actualizar el objeto.",
                "difficulty": "Medio",
                "base_code": "# Clase Hora con manejo de tiempo\nclass Hora:\n    # Constructor(hr, min, seg)\n    # mostrarHora() - formato hh:mm:ss\n    # horaSig() - muestra hora + 1 segundo\n    # actualizarHora() - modifica el objeto\n    pass\n\nh = Hora(23, 59, 59)\nh.mostrarHora()\nh.actualizarHora()\nh.mostrarHora()\n"
            },
            {
                "id": "e-poo2-4", "topic_id": "poo-intermedia", "order": 4,
                "title": "Cuenta bancaria",
                "description": "Crear una clase CuentaBancaria con atributos privados (titular, saldo), métodos depositar, retirar (con validación de fondos) y mostrar_saldo.",
                "difficulty": "Medio",
                "base_code": "# Cuenta bancaria con encapsulamiento\nclass CuentaBancaria:\n    # Atributos privados: __titular, __saldo\n    # Métodos: depositar, retirar, mostrar_saldo\n    pass\n\ncuenta = CuentaBancaria('Carlos', 100)\ncuenta.depositar(50)\ncuenta.retirar(30)\ncuenta.retirar(200)\ncuenta.mostrar_saldo()\n"
            },
            {
                "id": "e-poo2-5", "topic_id": "poo-intermedia", "order": 5,
                "title": "Persona con encapsulamiento",
                "description": "Crear una clase Persona con atributos privados (nombre, apellido, edad) y métodos get/set para cada uno.",
                "difficulty": "Medio",
                "base_code": "# Persona con atributos privados y get/set\nclass Persona:\n    # Atributos privados\n    # Getters y setters para nombre, apellido, edad\n    pass\n\np = Persona()\np.setNombre('Lorena')\np.setApellido('Alonso')\nprint('Nombre', p.getNombre())\nprint('Apellido', p.getApellido())\n"
            },
            {
                "id": "e-poo2-6", "topic_id": "poo-intermedia", "order": 6,
                "title": "Número entero con get/set",
                "description": "Crear una clase NumEntero con atributo privado, métodos para verificar paridad, contar dígitos y sumar dígitos.",
                "difficulty": "Medio",
                "base_code": "# Clase NumEntero con operaciones\nclass NumEntero:\n    # Atributo privado __num\n    # Métodos: par(), cuatroDigitos(), sumaDigitos()\n    pass\n\nn = NumEntero(1234)\nn.par()\nn.cuatroDigitos()\nn.sumaDigitos()\n"
            },
            {
                "id": "e-poo2-7", "topic_id": "poo-intermedia", "order": 7,
                "title": "Manipulación de cadenas",
                "description": "Crear una clase Frase con métodos para contar caracteres, invertir la cadena, contar palabras y verificar palíndromos.",
                "difficulty": "Difícil",
                "base_code": "# Clase Frase para manipulación de cadenas\nclass Frase:\n    # Constructor(cadena)\n    # contarCaracter(c), mostrarInvertida()\n    # contarPalabras()\n    pass\n\nf = Frase('Hola mundo')\nf.contarCaracter('o')\nf.mostrarInvertida()\nf.contarPalabras()\n"
            },

            # --- ARREGLOS DE OBJETOS ---
            {
                "id": "e-ao-1", "topic_id": "arreglos-objetos", "order": 1,
                "title": "Calificaciones",
                "description": "Crear una clase Calificaciones que almacene n calificaciones en un arreglo y calcule el promedio.",
                "difficulty": "Fácil",
                "base_code": "# Clase para manejar calificaciones\nclass Calificaciones:\n    # Constructor(n), guardar(), promedio()\n    pass\n\nc = Calificaciones(5)\nc.guardar()\nc.promedio()\n"
            },
            {
                "id": "e-ao-2", "topic_id": "arreglos-objetos", "order": 2,
                "title": "Puntajes de dado",
                "description": "Crear una clase Lanzamientos que simule n lanzamientos de dado con valores fijos y cuente las ocurrencias de un valor específico.",
                "difficulty": "Fácil",
                "base_code": "# Simulación de lanzamientos de dado (datos fijos)\nclass Lanzamientos:\n    def __init__(self):\n        self.datos = [3, 5, 2, 6, 1, 3, 4, 6, 2, 3]\n        self.total = len(self.datos)\n\n    def mostrar(self):\n        # Muestra todos los valores\n        pass\n\n    def contarValor(self, valor):\n        # Cuenta cuántas veces aparece 'valor'\n        pass\n\n# Programa principal\nlanz = Lanzamientos()\nlanz.mostrar()\nlanz.contarValor(3)\n"
            },
            {
                "id": "e-ao-3", "topic_id": "arreglos-objetos", "order": 3,
                "title": "Temperaturas",
                "description": "Crear una clase Temperatura con un arreglo de temperaturas fijas y un método para convertirlas a Fahrenheit.",
                "difficulty": "Medio",
                "base_code": "# Clase para manejar temperaturas\nclass Temperatura:\n    def __init__(self):\n        self.celsius = [15, 22, 30, 8, 25, 18, 12]\n        self.total = len(self.celsius)\n\n    def mostrar(self):\n        # Muestra las temperaturas en Celsius\n        pass\n\n    def convertirF(self):\n        # Convierte a Fahrenheit: F = C * 9/5 + 32\n        pass\n\n# Programa principal\nt = Temperatura()\nt.mostrar()\nt.convertirF()\n"
            },
            {
                "id": "e-ao-4", "topic_id": "arreglos-objetos", "order": 4,
                "title": "Agenda telefónica",
                "description": "Crear una clase Persona (nombre, teléfono) y un programa que maneje un arreglo de personas con funcionalidad de búsqueda por nombre.",
                "difficulty": "Medio",
                "base_code": "# Agenda telefónica con arreglo de objetos\nclass Persona:\n    # Constructor(nombre, telefono)\n    # mostrar()\n    pass\n\n# Programa principal\nagenda = []\nagenda.append(Persona('Juan', '2281234567'))\nagenda.append(Persona('Maria', '2289876543'))\nagenda.append(Persona('Pedro', '2285551234'))\n# Muestra todos los contactos\n# Busca un contacto por nombre\n"
            },

            # --- ORDENAMIENTO ---
            {
                "id": "e-ord-1", "topic_id": "ordenamiento", "order": 1,
                "title": "Ordenamiento burbuja",
                "description": "Implementar el algoritmo de ordenamiento burbuja (intercambio directo) para ordenar un arreglo de menor a mayor.",
                "difficulty": "Medio",
                "base_code": "# Ordenamiento burbuja\nclass Coleccion:\n    def __init__(self):\n        self.datos = [15, 3, 8, 12, 1, 19, 7, 4, 11, 6]\n        self.total = len(self.datos)\n\n    def mostrar(self):\n        print(self.datos)\n\n    def ordenar(self):\n        # Implementa el algoritmo de burbuja\n        pass\n\n# Programa principal\nnum = Coleccion()\nprint('Antes:')\nnum.mostrar()\nnum.ordenar()\nprint('Después:')\nnum.mostrar()\n"
            },
            {
                "id": "e-ord-2", "topic_id": "ordenamiento", "order": 2,
                "title": "Selección directa",
                "description": "Implementar el algoritmo de selección directa para ordenar un arreglo de menor a mayor.",
                "difficulty": "Medio",
                "base_code": "# Ordenamiento por selección directa\nclass Coleccion:\n    def __init__(self):\n        self.datos = [15, 3, 8, 12, 1, 19, 7, 4, 11, 6]\n        self.total = len(self.datos)\n\n    def mostrar(self):\n        print(self.datos)\n\n    def ordenar(self):\n        # Implementa selección directa\n        pass\n\n# Programa principal\nnum = Coleccion()\nprint('Antes:')\nnum.mostrar()\nnum.ordenar()\nprint('Después:')\nnum.mostrar()\n"
            },
        ]

        # =============================================
        # 3. CASOS DE PRUEBA (Test Cases)
        # =============================================
        test_cases_data = [
            # --- SECUENCIAL ---
            {"exercise_id": "e-sec-1", "input_data": "10\n5", "expected_output": "25.0", "is_hidden": False},
            {"exercise_id": "e-sec-1", "input_data": "6\n4", "expected_output": "12.0", "is_hidden": True},
            {"exercise_id": "e-sec-2", "input_data": "3\n2", "expected_output": "14", "is_hidden": False},
            {"exercise_id": "e-sec-3", "input_data": "3\n4", "expected_output": "21", "is_hidden": False},
            {"exercise_id": "e-sec-4", "input_data": "3661", "expected_output": "1 1 1", "is_hidden": False},
            {"exercise_id": "e-sec-4", "input_data": "75", "expected_output": "0 1 15", "is_hidden": True},
            {"exercise_id": "e-sec-5", "input_data": "5\n10", "expected_output": "5 10\n10 5", "is_hidden": False},
            {"exercise_id": "e-sec-6", "input_data": "5\n8", "expected_output": "1.7272", "is_hidden": False},

            # --- SELECTIVA ---
            {"exercise_id": "e-sel-1", "input_data": "10\n5\n8", "expected_output": "El mayor es:  10", "is_hidden": False},
            {"exercise_id": "e-sel-1", "input_data": "3\n9\n6", "expected_output": "El mayor es:  9", "is_hidden": True},
            {"exercise_id": "e-sel-2", "input_data": "4", "expected_output": "Es número par", "is_hidden": False},
            {"exercise_id": "e-sel-2", "input_data": "7", "expected_output": "Es número impar", "is_hidden": True},
            {"exercise_id": "e-sel-3", "input_data": "15", "expected_output": "Es múltiplo de 5", "is_hidden": False},
            {"exercise_id": "e-sel-3", "input_data": "7", "expected_output": "No es múltiplo de 5", "is_hidden": True},
            {"exercise_id": "e-sel-4", "input_data": "45\n100", "expected_output": "4500.0", "is_hidden": False},
            {"exercise_id": "e-sel-5", "input_data": "8\n59\n59", "expected_output": "9:0:0", "is_hidden": False},

            # --- REPETITIVA ---
            {"exercise_id": "e-rep-1", "input_data": "5", "expected_output": "1\n2\n3\n4\n5", "is_hidden": False},
            {"exercise_id": "e-rep-2", "input_data": None, "expected_output": "suma de pares:  10100\nsuma de impares:  10000", "is_hidden": False},
            {"exercise_id": "e-rep-3", "input_data": "5", "expected_output": "15", "is_hidden": False},
            {"exercise_id": "e-rep-4", "input_data": "3", "expected_output": "30", "is_hidden": False},
            {"exercise_id": "e-rep-5", "input_data": "3\n10\n20\n30", "expected_output": "20.0", "is_hidden": False},

            # --- ARREGLOS ---
            {"exercise_id": "e-arr-1", "input_data": "3\n10\n20\n30", "expected_output": "[10, 20, 30]", "is_hidden": False},
            {"exercise_id": "e-arr-2", "input_data": "10", "expected_output": "[2, 5, 8, 10, 12, 20]", "is_hidden": False},

            # --- MATRICES ---
            {"exercise_id": "e-mat-1", "input_data": None, "expected_output": "[10, 10, 10]\n[10, 10, 10]\n[10, 10, 10]", "is_hidden": False},
            {"exercise_id": "e-mat-2", "input_data": None, "expected_output": "[1, 4, 7]\n[2, 5, 8]\n[3, 6, 9]", "is_hidden": False},
            {"exercise_id": "e-mat-3", "input_data": None, "expected_output": "100\n42\n100", "is_hidden": False},

            # --- POO BASICA ---
            {"exercise_id": "e-poo1-1", "input_data": None, "expected_output": "¡Guau!\nCorriendo...\nGuau, soy  Max", "is_hidden": False},
            {"exercise_id": "e-poo1-2", "input_data": None, "expected_output": "El área es  25\nEl perímeto es:  20", "is_hidden": False},
            {"exercise_id": "e-poo1-3", "input_data": None, "expected_output": "Hola, soy  Lorena\nHola, soy  David\nHola, soy  Carlos\nLa nueva edad de  Carlos  es  16", "is_hidden": False},
            {"exercise_id": "e-poo1-4", "input_data": "5", "expected_output": "El área es 25\nEl perímetro es  20", "is_hidden": False},
            {"exercise_id": "e-poo1-5", "input_data": "1234", "expected_output": "Si es de 4 dígitos\nEl dígito de las unidades es:  4\nLa suma es:  10", "is_hidden": False},
            {"exercise_id": "e-poo1-6", "input_data": None, "expected_output": "Segundo nombre  Carlos\nSegundo nombre ", "is_hidden": False},

            # --- POO INTERMEDIA ---
            {"exercise_id": "e-poo2-1", "input_data": None, "expected_output": "El área es  25\nEl perímeto es:  20\nEl área es  9\nEl perímeto es:  12", "is_hidden": False},
            {"exercise_id": "e-poo2-2", "input_data": "5", "expected_output": "El área es  25\nEl perímeto es:  20", "is_hidden": False},
            {"exercise_id": "e-poo2-3", "input_data": None, "expected_output": "23:59:59\n0:0:0", "is_hidden": False},
            {"exercise_id": "e-poo2-4", "input_data": None, "expected_output": "Fondos insuficientes.\nSaldo actual de Carlos :  120", "is_hidden": False},
            {"exercise_id": "e-poo2-5", "input_data": None, "expected_output": "Nombre Lorena\nApellido Alonso", "is_hidden": False},
            {"exercise_id": "e-poo2-6", "input_data": None, "expected_output": "El número es par\nEl número SI tiene 4 dígitos\nLa suma de los dígitos es  10", "is_hidden": False},
            {"exercise_id": "e-poo2-7", "input_data": None, "expected_output": "2\nodnum aloH\n2", "is_hidden": False},

            # --- ARREGLOS DE OBJETOS ---
            {"exercise_id": "e-ao-1", "input_data": "3\n85\n90\n95", "expected_output": "90.0", "is_hidden": False},
            {"exercise_id": "e-ao-2", "input_data": None, "expected_output": "[3, 5, 2, 6, 1, 3, 4, 6, 2, 3]\n3 aparece 3 veces", "is_hidden": False},
            {"exercise_id": "e-ao-3", "input_data": None, "expected_output": "59.0\n71.6\n86.0\n46.4\n77.0\n64.4\n53.6", "is_hidden": False},
            {"exercise_id": "e-ao-4", "input_data": None, "expected_output": "Juan 2281234567\nMaria 2289876543\nPedro 2285551234", "is_hidden": False},

            # --- ORDENAMIENTO ---
            {"exercise_id": "e-ord-1", "input_data": None, "expected_output": "Antes:\n[15, 3, 8, 12, 1, 19, 7, 4, 11, 6]\nDespués:\n[1, 3, 4, 6, 7, 8, 11, 12, 15, 19]", "is_hidden": False},
            {"exercise_id": "e-ord-2", "input_data": None, "expected_output": "Antes:\n[15, 3, 8, 12, 1, 19, 7, 4, 11, 6]\nDespués:\n[1, 3, 4, 6, 7, 8, 11, 12, 15, 19]", "is_hidden": False},
        ]

        # --- PROCESO DE ACTUALIZACIÓN (UPSERT) ---

        # Actualización de Temas
        for t in topics_data:
            existing_topic = db.query(models.Topic).filter(models.Topic.id == t["id"]).first()
            if existing_topic:
                for key, value in t.items():
                    setattr(existing_topic, key, value)
            else:
                db.add(models.Topic(**t))

        # Actualización de Ejercicios
        for e in exercises_data:
            existing_exercise = db.query(models.Exercise).filter(models.Exercise.id == e["id"]).first()
            if existing_exercise:
                for key, value in e.items():
                    setattr(existing_exercise, key, value)
            else:
                db.add(models.Exercise(**e))

        # Actualización de Casos de Prueba
        for tc in test_cases_data:
            existing_tc = db.query(models.TestCase).filter(
                models.TestCase.exercise_id == tc["exercise_id"],
                models.TestCase.input_data == tc["input_data"]
            ).first()
            if existing_tc:
                existing_tc.expected_output = tc["expected_output"]
                existing_tc.is_hidden = tc["is_hidden"]
            else:
                db.add(models.TestCase(**tc))

        db.commit()
        print("OK Base de datos ACTUALIZADA con exito.")
        print(f"   {len(topics_data)} temas")
        print(f"   {len(exercises_data)} ejercicios")
        print(f"   {len(test_cases_data)} casos de prueba")

    except Exception as e:
        print(f"ERROR al poblar la base de datos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
