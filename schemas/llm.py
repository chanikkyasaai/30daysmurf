from pydantic import BaseModel

class LLMQueryRequest(BaseModel):
    query: str

class LLMQueryResponse(BaseModel):
    response: str
