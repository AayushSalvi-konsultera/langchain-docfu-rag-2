from pydantic import BaseModel
from typing import Dict, Any 

class ChainContext(BaseModel):
    """Carries Langchain execution state across MCP calls"""
    memory:dict = {}
    metadata:dict = {} 