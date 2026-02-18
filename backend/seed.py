import json
from backend.infra.db import SessionLocal, engine, Base
from backend.core import models

def seed_data():
    # Crea las tablas si no existen
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
            }
        ]

        # 2. EJERCICIOS COMPLETOS (Exercises)
        exercises_data = [
            {"id": "e1", "topic_id": "intro-python", "title": "Hola Mundo", "description": "Imprime tu primer mensaje en consola.", "difficulty": "Fácil"},
            {"id": "e2", "topic_id": "intro-python", "title": "Variables Numéricas", "description": "Crea variables y suma dos números.", "difficulty": "Fácil"},
            {"id": "e3", "topic_id": "control-flujo", "title": "Es mayor de edad", "description": "Usa if/else para verificar una edad.", "difficulty": "Fácil"}
        ]

        # 4. CASOS DE PRUEBA (Test Cases)
        test_cases_data = [
            {"exercise_id": "e1", "input_data": None, "expected_output": "Hola Mundo", "is_hidden": False},
            {"exercise_id": "e2", "input_data": None, "expected_output": "15", "is_hidden": False},
            {"exercise_id": "e3", "input_data": "15", "expected_output": "Eres menor de edad", "is_hidden": False},
            {"exercise_id": "e3", "input_data": "20", "expected_output": "Eres mayor de edad", "is_hidden": True}
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
        print("✅ Base de datos ACTUALIZADA con éxito.")

    except Exception as e:
        print(f"❌ Error al poblar la base de datos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()