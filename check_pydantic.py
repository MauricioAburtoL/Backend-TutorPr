import pydantic
print(f"Pydantic Version: {pydantic.VERSION}")
try:
    from pydantic import BaseModel
    m = BaseModel()
    print(f"Has model_dump_json: {hasattr(m, 'model_dump_json')}")
    print(f"Has json: {hasattr(m, 'json')}")
except Exception as e:
    print(e)
