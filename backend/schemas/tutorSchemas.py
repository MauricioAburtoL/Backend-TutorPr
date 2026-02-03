# backend/schemas/tutorSchemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from .baseSchemas import Lang
from .executionSchemas import ExecResult

class HintIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    userId: str = Field(alias="user_id") #
    sessionId: str = Field(alias="session_id") #
    exerciseId: str = Field(alias="exercise_id") #
    attemptId: str = Field(alias="attempt_id") #
    code: str #
    execResult: Optional[ExecResult] = Field(None, alias="exec_result") #
    lang: Optional[Lang] = "python" #

class HintOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    hint: str #
    patternId: str = Field(alias="pattern_id") #
    concept: str = "" #