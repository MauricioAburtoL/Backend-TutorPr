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
    print("🚀 Tablas de la base de datos verificadas/creadas.")