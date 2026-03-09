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
        Actua como un tutor de programacion. Analiza el siguiente codigo segun el contexto proporcionado.
        IMPORTANTE: Todas tus respuestas deben estar en ESPAÑOL.

        Contexto: {request.context}
        Lenguaje: {request.language}
        Codigo del estudiante:
        {request.studentCode}

        Debes retornar un objeto JSON VALIDO con la siguiente estructura:
        {{
          "status": "error" | "success" | "warning",
          "pedagogical_feedback": "Guia socratica en español...",
          "technical_hints": ["Pista 1 en español", "Pista 2 en español"],
          "detected_errors": [{{"line": <int>, "type": "logic|syntax", "desc": "descripcion en español"}}],
          "mermaid_chart": "graph TD; ...",
          "next_step_question": "Pregunta en español para guiar al estudiante..."
        }}

        Proporciona retroalimentacion pedagogica que guie al estudiante sin darle la respuesta directa.
        Asegurate de que 'mermaid_chart' sea un string valido de Mermaid JS para un diagrama de flujo que represente la logica del codigo.
        Todos los textos en los campos JSON deben estar en ESPAÑOL.
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
