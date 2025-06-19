from pydantic import BaseModel
from enum import Enum
from typing import Optional, List


class ProcessRequest(BaseModel):
    user_q: str
    faq_q: Optional[str] = None
    intent: Optional[str] = None
    entity: Optional[str] = None
    concept: Optional[List[str]] = None

class ProcessResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float


class RouteDecision(Enum):
    RAG = "rag"
    MCP = "mcp"
    DIRECT_RESPONSE = "direct_response"