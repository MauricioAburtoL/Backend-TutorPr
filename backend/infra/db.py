#infra/db.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Configuración de la Base de Datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///events.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# 2. Creación del motor y la sesión
engine = create_engine(DATABASE_URL, echo=False, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Definición de la Base (Debe estar ANTES de cualquier importación de modelos)
Base = declarative_base()

def get_db():
    """Generador de sesiones para los endpoints de FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Inicializa la base de datos creando las tablas necesarias"""
    # IMPORTANTE: La importación debe ser local y absoluta para evitar el ciclo
    from backend.core import models 
    
    # Esto busca todas las clases que heredan de Base en models.py y las crea
    Base.metadata.create_all(bind=engine)
    # Los contratos del catálogo son versionados e idempotentes. Sincronizarlos
    # al arrancar permite activar el ejercicio de control sin depender de una
    # recreación manual de la base existente.
    from backend.core.evaluation.catalog import (
        PUBLISHED_EXERCISE_CONTRACTS,
        PUBLISHED_EXERCISE_STARTERS,
        PUBLISHED_EXERCISE_TOPICS,
        PUBLISHED_EXERCISES,
    )
    from backend.core.evaluation.contracts import ExerciseContractDefinition

    db = SessionLocal()
    try:
        for topic_data in PUBLISHED_EXERCISE_TOPICS:
            topic = db.query(models.Topic).filter(
                models.Topic.id == topic_data["id"],
            ).first()
            if topic is None:
                db.add(models.Topic(**topic_data))
            else:
                for key, value in topic_data.items():
                    setattr(topic, key, value)

        db.flush()
        for exercise_data in PUBLISHED_EXERCISES:
            exercise = db.query(models.Exercise).filter(
                models.Exercise.id == exercise_data["id"],
            ).first()
            if exercise is None:
                db.add(models.Exercise(**exercise_data))
            else:
                for key, value in exercise_data.items():
                    setattr(exercise, key, value)

        db.flush()
        for raw_contract in PUBLISHED_EXERCISE_CONTRACTS:
            contract = ExerciseContractDefinition.model_validate(raw_contract)
            definition = contract.model_dump(mode="json", by_alias=True)
            exercise = db.query(models.Exercise).filter(
                models.Exercise.id == contract.exercise_id,
            ).first()
            if exercise is None:
                # En una base recién creada, seed_data insertará primero el
                # ejercicio y después su contrato. Esto evita una referencia
                # foránea inválida en motores que sí la aplican al arrancar.
                continue
            starter_code = PUBLISHED_EXERCISE_STARTERS.get(contract.exercise_id)
            if starter_code is not None:
                exercise.base_code = starter_code
            stored = db.query(models.ExerciseContract).filter(
                models.ExerciseContract.exercise_id == contract.exercise_id,
                models.ExerciseContract.version == contract.contract_version,
            ).first()
            if stored:
                stored.status = "published"
                stored.definition = definition
            else:
                db.add(models.ExerciseContract(
                    exercise_id=contract.exercise_id,
                    version=contract.contract_version,
                    status="published",
                    definition=definition,
                ))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print("🚀 Tablas de la base de datos verificadas/creadas.")
