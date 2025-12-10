# backend/schemas/schemas.py
from typing import Optional, Literal, List, Tuple, Dict, Any
from pydantic import BaseModel, Field

# Alias para el lenguaje
Lang = Literal["python", "java", "cpp"]

class ExecuteIn(BaseModel):
    user_id: str
    session_id: str
    exercise_id: str
    attempt_id: str
    code: str

class ExecResult(BaseModel):
    status: str
    stdout: str = ""
    stderr: str = ""
    error_type: Optional[str] = None
    runtime_ms: Optional[int] = None

class HintIn(BaseModel):
    user_id: str
    session_id: str
    exercise_id: str
    attempt_id: str
    code: str
    exec_result: Optional[ExecResult] = None
    lang: Optional[Lang] = "python"   # usa el alias

class HintOut(BaseModel):
    hint: str
    pattern_id: str
    concept: str = ""

# Para /api/cfg con lang en el body (si lo usas)
class CodeIn(BaseModel):
    code: str
    lang: Lang = "python"              # <-- corrige esto

# Para /api/cfg/{lang} con body { code }
class CodeOnly(BaseModel):
    code: str

class CFGOut(BaseModel):
    language: str
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Tuple[str, str]] = Field(default_factory=list)
    mermaid: Optional[str] = None
