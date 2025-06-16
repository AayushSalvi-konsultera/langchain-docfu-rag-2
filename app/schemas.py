from pydantic import BaseModel

class ProcessRequest(BaseModel):
    user_q: str
    faq_q: str
    intent: str
    entity: str
    concept: str

class ProcessResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float