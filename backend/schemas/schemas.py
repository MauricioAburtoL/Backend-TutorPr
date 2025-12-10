from pydantic import BaseModel
from typing import Optional, List, Dict, Any

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
    exec_result: ExecResult

class HintOut(BaseModel):
    hint: str
    pattern_id: str
    concept: str
    detector: str = "rules"
    confidence: float = 1.0

class CFGOut(BaseModel):
    language: str
    mermaid: str
    nodes: List[Dict[str, Any]]
    
class CodeIn(BaseModel):
    lang: str
    code: str
