# backend/api/auth.py
import hashlib
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..infra.db import get_db
from ..core.models import User
from ..schemas import LoginIn, LoginOut

router = APIRouter()


def hash_password(password: str) -> str:
    """Hash de contrasena (prototipo). En produccion usar bcrypt/passlib."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@router.post("/auth/login", response_model=LoginOut, response_model_by_alias=False)
def login(body: LoginIn, db: Session = Depends(get_db)):
    """
    Autentica contra la tabla users (sembrada en seed.py, sin auto-registro).
    Devuelve el user_id para que el frontend asocie correctamente ejecuciones,
    pistas y estadisticas al estudiante.
    """
    user = db.query(User).filter(User.username == body.username).first()
    if not user or user.password_hash != hash_password(body.password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    return LoginOut(user_id=user.user_id, username=user.username, role=user.role)
