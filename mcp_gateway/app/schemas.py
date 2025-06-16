from pydantic import BaseModel
from typing import Dict, Any

class ToolRegistrationRequest(BaseModel):
    tool_name: str
    tool_service_url: str
    description: str = ""
    parameters: Dict[str,str] = {}
