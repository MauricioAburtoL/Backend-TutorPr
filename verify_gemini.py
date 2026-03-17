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
        context="#Escribir una clase para almacenar un número entero con los siguientes métodos: Validar si el número es de 4 dígitos Determinar el dígito de las unidades Determinar la suma de sus dígitos",
        language="Python",
        student_code="""class Numero:
    num = 0
    
    def __init__(self, n):
        self.num = n

    def validar(self):
        if self.num >999 and num <10000:
            print("Si es de 4 dígitos")
        else:
            print("No es de 4 dígitos")

    def digitoUnidad(self):
        unidad = self.num %10
        print("El dígito de las unidades es: ", unidad)

    def sumarDigitos(self):
        u = self.num %10
        queda = self.num // 10
        d = queda % 10
        queda = queda //10
        c = queda %10
        m = queda //10
        suma = u + d + c + m
        print("La suma es: ", suma)

    def ejemplo(self):
        x = self.num
        resp = 1
        while x >0:
            print(x)
            resp = resp * x
            x = x - 1
        print("El resultado es: ", resp)

#programa principal
print("introduce un número de 4 digitos")
num = int(input())

n1 = Numero(num)
n1.validar()
n1.digitoUnidad()
n1.sumarDigitos()

n1.ejemplo()
"""
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
