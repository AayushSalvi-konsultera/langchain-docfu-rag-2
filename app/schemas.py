from pydantic import BaseModel
from enum import Enum


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


class RouteDecision(Enum):
    RAG = "rag"
    MCP = "mcp"
    DIRECT_RESPONSE = "direct_response"