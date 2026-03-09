# backend/schemas/executionSchemas.py
import string
from typing import Optional, List, Tuple, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from .baseSchemas import Lang

class ExecuteIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    userId: str = Field(alias="user_id") #
    sessionId: str = Field(alias="session_id") #
    exerciseId: str = Field(alias="exercise_id") #
    attemptId: str = Field(alias="attempt_id") #
    code: str #
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
    exerciseId: Optional[str] = Field(default=None, alias="exercise_id")