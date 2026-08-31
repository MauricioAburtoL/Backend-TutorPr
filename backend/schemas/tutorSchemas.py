# backend/schemas/tutorSchemas.py
from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, Any, Dict, List
from .baseSchemas import Lang
from ..core.code_validation import has_meaningful_code

class HintIn(BaseModel):
    # 'extra="allow"' es vital para que no truene si Angular envia campos de mas
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    userId: str = Field(alias="user_id")
    sessionId: str = Field(alias="session_id")
    exerciseId: str = Field(alias="exercise_id")
    attemptId: str = Field(alias="attempt_id")
    code: str

    # Cambiamos ExecResult por Dict[str, Any] para que acepte cualquier objeto JSON
    execResult: Optional[Dict[str, Any]] = Field(default_factory=dict, alias="exec_result")
    lang: Optional[Lang] = "python"

    @model_validator(mode="after")
    def validate_meaningful_code(self):
        if not has_meaningful_code(self.code, self.lang or "python"):
            raise ValueError("Escribe alguna instrucción antes de solicitar una pista.")
        return self

class HintOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    hint: str
    patternId: str = Field(default="unknown", alias="pattern_id")
    concept: str = ""
    # Campos para integracion con Gemini
    source: str = "rules"  # "gemini" | "rules"
    hasMoreHints: bool = Field(default=False, alias="has_more_hints")
    detectedErrors: List[Dict[str, Any]] = Field(default_factory=list, alias="detected_errors")
