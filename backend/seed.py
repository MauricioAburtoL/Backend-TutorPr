import json
from backend.infra.db import SessionLocal, engine, Base
from backend.core import models

def seed_data():
    Base.metadata.create_all(bind=engine) 
    db = SessionLocal()
    try:
        # 1. TEMAS COMPLETOS (Topics)
        topics_data = [
            {
                "id": "intro-python",
                "title": "Introducción a Python",
                "description": "Domina la sintaxis esencial, variables y operaciones matemáticas.",
                "icon": "🐍",
                "category": "Fundamentos",
                "total_exercises": 5,
                "tags": ["Variables", "Tipos de Datos", "Input/Output"],
                "estimated_time": "1h 30m"
            },
            {
                "id": "control-flujo",
                "title": "Control de Flujo",
                "description": "Aprende a tomar decisiones lógicas en tu código.",
                "icon": "🔀",
                "category": "Lógica",
                "total_exercises": 10,
                "tags": ["If/Else", "Booleanos", "Comparadores"],
                "estimated_time": "2h 15m"
            },
            {
                "id": "ciclos",
                "title": "Ciclos y Bucles",
                "description": "Automatiza tareas repetitivas eficientemente.",
                "icon": "🔁",
                "category": "Lógica",
                "total_exercises": 8,
                "tags": ["For", "While", "Range", "Iteradores"],
                "estimated_time": "3h 00m"
            },
            {
                "id": "funciones",
                "title": "Funciones y Módulos",
                "description": "Organiza tu código en bloques reutilizables.",
                "icon": "🧩",
                "category": "Estructuras",
                "total_exercises": 6,
                "tags": ["Def", "Return", "Scope", "Parámetros"],
                "estimated_time": "4h 00m"
            }
        ]

        # 2. EJERCICIOS COMPLETOS (Exercises)
        exercises_data = [
            # Intro Python
            {"id": "e1", "topic_id": "intro-python", "title": "Hola Mundo", "description": "Imprime tu primer mensaje en consola.", "difficulty": "Fácil"},
            {"id": "e2", "topic_id": "intro-python", "title": "Variables Numéricas", "description": "Crea variables y suma dos números.", "difficulty": "Fácil"},
            # Control de Flujo
            {"id": "e3", "topic_id": "control-flujo", "title": "Es mayor de edad", "description": "Usa if/else para verificar una edad.", "difficulty": "Fácil"},
            {"id": "e4", "topic_id": "control-flujo", "title": "Calculadora de Descuentos", "description": "Aplica descuentos según el monto de compra.", "difficulty": "Medio"},
            {"id": "e5", "topic_id": "control-flujo", "title": "El semáforo", "description": "Decide qué hacer según el color.", "difficulty": "Fácil"},
            # Ciclos
            {"id": "e6", "topic_id": "ciclos", "title": "Contador del 1 al 10", "description": "Usa un ciclo for básico.", "difficulty": "Fácil"}
        ]

        # 3. PERFIL DE USUARIO DETALLADO (UserStats)
        user_id = "student_01"
        user_exists = db.query(models.UserStats).filter(models.UserStats.user_id == user_id).first()
        
        if not user_exists:
            initial_user = models.UserStats(
                user_id=user_id,
                username="Estudiante",
                level="Explorador de Python 🐍",
                exercises_completed=12,
                study_streak=3,
                total_hours=5.5,
                skills=[
                    {"name": "Lógica", "progress": 75},
                    {"name": "Sintaxis", "progress": 40},
                    {"name": "Depuración", "progress": 20},
                    {"name": "Algoritmos", "progress": 10}
                ],
                last_accessed={
                    "exerciseId": "e3",
                    "title": "Es mayor de edad",
                    "topicName": "Control de Flujo",
                    "progress": 50
                },
                daily_tip='💡 Tip: Usa "elif" cuando tengas múltiples condiciones encadenadas para ahorrar líneas de código.',
                mastery_score=45,
                weak_areas=['Bucles Anidados', 'Condicionales Compuestos'],
                strong_areas=['Declaración de Variables', 'Salida de Datos (Print)'],
                recommendations=[
                    {"title": 'Repasar la teoría de "Ciclos y Bucles"', "type": 'review', "link": '/topics'},
                    {"title": 'Resolver: "El semáforo" (Control de Flujo)', "type": 'practice', "link": '/solve/e5'}
                ]
            )
            db.add(initial_user)

        # Inserción de Temas
        for t in topics_data:
            if not db.query(models.Topic).filter(models.Topic.id == t["id"]).first():
                db.add(models.Topic(**t))

        # Inserción de Ejercicios
        for e in exercises_data:
            if not db.query(models.Exercise).filter(models.Exercise.id == e["id"]).first():
                db.add(models.Exercise(**e))

        db.commit()
        print("✅ Base de datos poblada con éxito con todos los datos de Angular.")

    except Exception as e:
        print(f"❌ Error al poblar la base de datos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()