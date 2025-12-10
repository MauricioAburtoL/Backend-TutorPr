from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Infra (base de datos)
from ..infra.db import engine, Base

# Routers de la capa API
from ..api import execute, hint, cfg, kpis #events


app = FastAPI(title="Edu Assistant API", version="0.3.0")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear tablas (solo si usas SQLAlchemy local)
Base.metadata.create_all(bind=engine)

# Registrar rutas
app.include_router(execute.router, prefix="/api", tags=["execute"])
app.include_router(hint.router,    prefix="/api", tags=["hint"])
app.include_router(cfg.router,     prefix="/api", tags=["cfg"])
app.include_router(kpis.router,    prefix="/api/kpis", tags=["kpis"])
# app.include_router(events.router,  prefix="/api", tags=["events"])


@app.get("/health")
def health():
    return {"ok": True}
