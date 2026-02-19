# backend/api/assist.py
from fastapi import APIRouter, HTTPException, Depends
from backend.schemas.geminiSchemas import AssistRequest, AssistResponse
from backend.core.services.GeminiTutoringService import GeminiTutoringService

router = APIRouter()
service = GeminiTutoringService()

@router.post("/assist", response_model=AssistResponse)
def assist_student(request: AssistRequest):
    """
    Endpoint para proveer asistencia pedagógica usando Gemini.
    """
    response = service.analyze_code(request)
    
    if not response:
        raise HTTPException(status_code=500, detail="Error processing request with Gemini")
        
    return response
