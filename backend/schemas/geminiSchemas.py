# backend/schemas/geminiSchemas.py
from pydantic import BaseModel, Field
try:
    from pydantic import ConfigDict
except ImportError:
    ConfigDict = None

from typing import List, Optional

# Helper to create config that works in both V1 and V2 (V2 supports class Config for migration)
class BaseSchema(BaseModel):
    class Config:
        populate_by_name = True
        allow_population_by_field_name = True

class AssistRequest(BaseSchema):
    context: str
    language: str
    studentCode: str = Field(alias="student_code")
    studentContext: Optional[str] = Field(default="", alias="student_context")
    # Veredicto ya emitido por el evaluador y salida observada del programa.
    # Evitan que el modelo tenga que deducir por su cuenta si la solución falló.
    evaluationStatus: Optional[str] = Field(default=None, alias="evaluation_status")
    programOutput: Optional[str] = Field(default="", alias="program_output")
    programError: Optional[str] = Field(default="", alias="program_error")

class DetectedError(BaseSchema):
    line: int
    type: str
    desc: str

class AssistResponse(BaseSchema):
    status: str # "error" | "success" | "warning"
    pedagogicalFeedback: str = Field(alias="pedagogical_feedback")
    technicalHints: List[str] = Field(alias="technical_hints")
    detectedErrors: List[DetectedError] = Field(alias="detected_errors")
    # El diagrama solo se solicita cuando el consumidor va a usarlo; el flujo de
    # pistas no lo consume y el visor de flujo se genera localmente.
    mermaidChart: str = Field(default="", alias="mermaid_chart")
    nextStepQuestion: str = Field(alias="next_step_question")
