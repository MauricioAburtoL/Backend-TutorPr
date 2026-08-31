# backend/schemas/executionSchemas.py
import string
from typing import Optional, List, Tuple, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator
from .baseSchemas import Lang
from ..core.code_validation import has_meaningful_code

class ExecuteIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    userId: str = Field(alias="user_id") #
    sessionId: str = Field(alias="session_id") #
    exerciseId: str = Field(alias="exercise_id") #
    attemptId: str = Field(alias="attempt_id") #
    code: str #
    lang: Lang = "python"
    durationMs: Optional[int] = Field(default=0, alias="duration_ms") #

class ExecResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    status: str #
    stdout: str = "" #
    stderr: str = "" #
    errorType: Optional[str] = Field(None, alias="error_type") #
    runtimeMs: Optional[int] = Field(None, alias="runtime_ms") #

class CodeIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    code: str #
    lang: Lang = "python" #

class CodeOnly(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    code: str #
    
class CFGOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    language: str
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Tuple[str, str]] = Field(default_factory=list)
    mermaid: Optional[str] = None
    source: str = "ast"  # "ast" | "gemini"

class CFGRequest(BaseModel):
    """Extiende CodeIn con contexto de usuario para buscar en cache de Gemini."""
    model_config = ConfigDict(populate_by_name=True)
    code: str
    lang: Lang = "python"
    userId: Optional[str] = Field(default=None, alias="user_id")
    sessionId: Optional[str] = Field(default=None, alias="session_id")
    exerciseId: Optional[str] = Field(default=None, alias="exercise_id")
    attemptId: Optional[str] = Field(default=None, alias="attempt_id")

    @model_validator(mode="after")
    def validate_meaningful_code(self):
        if not has_meaningful_code(self.code, self.lang):
            raise ValueError("Escribe alguna instrucción antes de generar el diagrama.")
        return self


class TelemetryEventIn(BaseModel):
    """Evento iniciado directamente por la interfaz de evaluación."""

    model_config = ConfigDict(populate_by_name=True)
    userId: str = Field(alias="user_id")
    sessionId: str = Field(alias="session_id")
    exerciseId: str = Field(alias="exercise_id")
    event: Literal["TaskStarted"]
    payload: Dict[str, Any] = Field(default_factory=dict)
