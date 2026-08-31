from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()
from backend.infra.db import init_db

# Infra (base de datos)
from backend.infra.db import engine, Base

# Routers de la capa API
from backend.api import execute, hint, cfg, kpis, assist, auth, events


app = FastAPI(
    title="Edu Assistant API - MSICU", 
    version="0.3.0",
    description="Sistema inteligente para el apoyo del aprendizaje de programación"
)

@app.on_event("startup")
def on_startup():
    """
    Inicializa la base de datos SQLite y crea las tablas 
    (Topics, Exercises, UserStats, Events) al arrancar.
    """
    init_db()

# Middleware CORS: Esencial para conectar con tu Frontend en Angular
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rutas (Endpoints)
app.include_router(execute.router, prefix="/api", tags=["Execution Service"])
app.include_router(hint.router,    prefix="/api", tags=["Tutor Agent / Hints"])
app.include_router(cfg.router,     prefix="/api", tags=["Static Analysis (CFG)"])
app.include_router(kpis.router,    prefix="/api/kpis", tags=["Learning Analytics"])
app.include_router(assist.router,  prefix="/api", tags=["Gemini AI Assistant"])
app.include_router(auth.router,    prefix="/api", tags=["Auth"])
app.include_router(events.router,  prefix="/api", tags=["Telemetry"])

@app.get("/health")
def health():
    """Endpoint de verificación de estado del backend"""
    return {"status": "online", "database": "connected"}



#comandos para ejecutar 
#windows
# # 1) Crear y activar entorno virtual
# python -m venv .venv
# .\.venv\Scripts\Activate.ps1

# # 2) Instalar dependencias (ajusta si tu requirements.txt tiene otras)
# pip install -r requirements.txt
# # Si está vacío, instala mínimo:
# pip install "fastapi>=0.110" "uvicorn[standard]>=0.27" "SQLAlchemy>=2.0" "pydantic>=2.5"

# # 3) Iniciar el servidor (puerto 8000)
# uvicorn backend.app.main:app --reload --port 8000

# IoS
# 1) Crear y activar entorno virtual
# python3 -m venv .venv
# source .venv/bin/activate

# # 2) Instalar dependencias
# pip3 install -r requirements.txt
# # Si está vacío, instala mínimo:
# pip3 install "fastapi>=0.110" "uvicorn[standard]>=0.27" "SQLAlchemy>=2.0" "pydantic>=2.5"

# # 3) Iniciar el servidor (puerto 8000)
# python3 -m uvicorn backend.app.main:app --reload --port 8000
