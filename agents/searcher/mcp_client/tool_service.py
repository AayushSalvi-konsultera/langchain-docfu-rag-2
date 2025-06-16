from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import httpx
import os 
import sys
from dotenv import load_dotenv
load_dotenv()

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..')
)
sys.path.insert(0, PROJECT_ROOT)
print(PROJECT_ROOT)
from agents.searcher.service.web import Search
from agents.searcher.mcp_client.schemas import ToolRequest, ToolResponse

app = FastAPI(title="Searcher Agent")

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")

TOOLS ={
    "Searcher": {
        "function": Search,
        "description": "Gives search result for given query",
        "parameters": {"query":"str"}
    }
}

    
# API Endpoints

@app.get("/")
async def root():
    return {
        "Message" : "Tool Service is running", 
        "available_tools" : list(TOOLS.keys())
    }


@app.post("tools/{tool_name}")
async def execute_tool(tool_name: str, request: ToolRequest) -> ToolResponse:
    """Execute a specific tool"""
    if tool_name not in TOOLS:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name} not found")
    
    try:
        tool_info = TOOLS[tool_name]
        tool_function = tool_info["function"]
        link, summary = tool_function(**request.user_q)

        return ToolResponse(link=link,
                            summary= summary)

    
    except Exception as e:
        return ToolResponse(link= None, summary= str(e))


@app.post("/register-with-mcp")
async def register_with_mcp():
    failed_tool = []
    registered_tools = []
    for tool_name, tool_info in TOOLS.items():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{MCP_SERVER_URL}/admin/register-tool",
                    json={
                        "tool_name" : tool_name,
                        "tool_service_url" : os.getenv('K_SERVICE','http://0.0.0.0:8000'),
                        "description": tool_info["description"],
                        "parameters" : tool_info["parameters"]
                    },
                    timeout=10.0
                )
                if response.status_code == 200:
                    registered_tools.append(tool_name)
                else:
                    failed_tool.append(f"{tool_name}: {response.text}")

        except Exception as e:
            failed_tool.append(f"{tool_name}:{str(e)}")

    
    return {
        "registered": registered_tools,
        "failed": failed_tool,
        "total_tools": len(TOOLS)
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy",
            "service": "tool-service"
            }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,host="0.0.0.0",port=int(os.environ.get("PORT",8000)))

    