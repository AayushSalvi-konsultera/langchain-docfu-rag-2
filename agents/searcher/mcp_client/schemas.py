from pydantic import BaseModel
from typing import Dict, Any

class ToolRequest(BaseModel):
    user_q: Any

class ToolResponse(BaseModel):
    link: Any
    summary: Any