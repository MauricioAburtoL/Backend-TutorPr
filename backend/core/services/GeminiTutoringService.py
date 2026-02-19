# backend/core/services/GeminiTutoringService.py
import os
import json
import google.generativeai as genai
from typing import Dict, Any
from backend.schemas.geminiSchemas import AssistRequest, AssistResponse

class GeminiTutoringService:
    def __init__(self):
        # Configurar la API Key desde variables de entorno
        # Se recomienda asegurar que GEMINI_API_KEY esté seteada en el sistema
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("Warning: GEMINI_API_KEY not found in environment variables.")
        else:
            genai.configure(api_key=self.api_key)

    def analyze_code(self, request: AssistRequest) -> AssistResponse:
        """
        Envia el contexto y código a Gemini para obtener feedback estructurado.
        """
        if not self.api_key:
             return self._create_error_response("Gemini API Key missing")

        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = self._build_prompt(request)

        try:
            # Solicitar respuesta en formato JSON
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            response_text = response.text
            data = json.loads(response_text)
            
            # Validar y retornar usando el esquema Pydantic
            # V2 usa model_validate, V1 usa parse_obj o **kwargs
            if hasattr(AssistResponse, "model_validate"):
                return AssistResponse.model_validate(data)
            else:
                return AssistResponse.parse_obj(data)

        except Exception as e:
            msg = str(e)
            if "429" in msg or "ResourceExhausted" in msg:
                 msg = "Gemini API Quota Exceeded. Please try again later."
            
            print(f"Error calling Gemini: {msg}")
            return self._create_error_response(msg)

    def _build_prompt(self, request: AssistRequest) -> str:
        return f"""
        Act as a programming tutor. Analyze the following code based on the context provided.
        
        Context: {request.context}
        Language: {request.language}
        Student Code:
        {request.studentCode}
        
        You MUST return a VALID JSON object with the following structure:
        {{
          "status": "error" | "success" | "warning",
          "pedagogical_feedback": "Socratic guidance text...",
          "technical_hints": ["Hint 1", "Hint 2"],
          "detected_errors": [{{"line": <int>, "type": "logic|syntax", "desc": "description"}}],
          "mermaid_chart": "graph TD; ...",
          "next_step_question": "What would happen if...?"
        }}
        
        Provide pedagogical feedback that guides the student rather than giving the answer.
        Ensure 'mermaid_chart' is a valid Mermaid JS string for a flowchart representing the code logic.
        """

    def _create_error_response(self, error_msg: str) -> AssistResponse:
        return AssistResponse(
            status="error",
            pedagogical_feedback=f"System Error: {error_msg}",
            technical_hints=[],
            detected_errors=[],
            mermaid_chart="",
            next_step_question=""
        )
