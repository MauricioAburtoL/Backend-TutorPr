# verify_gemini.py
import os
import sys

# Add the current directory to sys.path to make backend imports work
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from backend.schemas.geminiSchemas import AssistRequest
from backend.core.services.GeminiTutoringService import GeminiTutoringService

def test_gemini_service():
    print("Testing GeminiTutoringService...")
    
    # Check for API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set. Please set it to run the verification.")
        return

    service = GeminiTutoringService()
    
    # Create a mock request
    request = AssistRequest(
        context="Ejercicio: Crear un bucle que sume números del 1 al 10.",
        language="Python",
        student_code="sum = 0\nfor i in range(10):\nsum = i"
    )
    
    # Handle Pydantic V1 vs V2
    if hasattr(request, "model_dump_json"):
        payload = request.model_dump_json(indent=2)
    else:
        payload = request.json(indent=2)
        
    print(f"Sending request: {payload}")
    
    try:
        response = service.analyze_code(request)
        if response:
            print("\n✅ Response received:")
            if hasattr(response, "model_dump_json"):
                print(response.model_dump_json(indent=2))
            else:
                print(response.json(indent=2))
            
            if response.status in ["success", "error", "warning"]:
                print("\n✅ Status validation passed.")
            else:
                print(f"\n❌ Status validation failed: {response.status}")
        else:
             print("\n❌ Response is None (Service Error)")
            
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")

if __name__ == "__main__":
    test_gemini_service()
