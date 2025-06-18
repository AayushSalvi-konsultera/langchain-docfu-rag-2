from pydantic import BaseModel
from typing import Dict, Any,Optional,List

class ToolRequest(BaseModel):
    user_q: Any
    num_results: Optional[int] = 10

class ToolResponse(BaseModel):
    results: Optional[List[Dict[str, str]]] = None
