from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.infra.db import init_db

# Infra (base de datos)
from backend.infra.db import engine, Base

# Routers de la capa API
from backend.api import execute, hint, cfg, kpis #events


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

@app.get("/health")
def health():
    """Endpoint de verificación de estado del backend"""
    return {"status": "online", "database": "connected"}