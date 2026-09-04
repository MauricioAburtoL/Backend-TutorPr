# backend/api/assist.py
from fastapi import APIRouter, HTTPException
from backend.schemas.geminiSchemas import AssistRequest, AssistResponse
from backend.core.services.GeminiTutoringService import GeminiTutoringService

router = APIRouter()
service = GeminiTutoringService()

@router.post("/assist", response_model=AssistResponse)
def assist_student(request: AssistRequest):
    """
    Endpoint para proveer asistencia pedagógica usando Gemini.

    Es el único consumidor del campo `mermaid_chart`, por lo que aquí sí se
    solicita el diagrama. El flujo de pistas no lo usa: su visor de flujo se
    genera localmente en `/api/cfg`.
    """
    response = service.analyze_code(request, include_diagram=True)
    
    if not response:
        raise HTTPException(status_code=500, detail="Error processing request with Gemini")
        
    return response
