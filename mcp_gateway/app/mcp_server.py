from fastmcp import FastMCP
from fastapi import FastAPI, HTTPException
import os
import asyncio
from typing import Dict, Any, Callable
import httpx
from contextlib import asynccontextmanager
from dotenv import load_dotenv
load_dotenv()


from schemas import ToolRegistrationRequest

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Auto-discover and register tools on startup"""
    print("MCP Server starting up...")

    # Try to auto-discover tools if TOOL_SERVICE_URL is set
    if TOOL_SERVICE_URL and TOOL_SERVICE_URL != "http://0.0.0.0:8000":
        try:
            await asyncio.sleep(2)  # Give tool service time to start
            result = await discover_and_register_tools()
            print(f"Startup discovery: {result['summary']}")
        except Exception as e:
            print(f"Startup discovery failed: {e}")

    yield  # ← the point where the app runs

mcp = FastMCP("agent-server")
app = FastAPI(title="MCP Server",lifespan=lifespan)

TOOL_SERVICE_URL = os.getenv("TOOL_SERVICE_URL","http://0.0.0.0:8000")

registered_tools: Dict[str, Dict[str, Any]] = {}

# def create_proxy_tool(tool_name: str, service_url: str, description: str):
#     """Dynamically created proxy tool"""

#     async def proxy_tool(**kwargs) -> Any:
#         try:
#             async with httpx.AsyncClient(timeout=10.0) as client:
#                 response = await client.post(
#                     f"{service_url}/tools/{tool_name}",
#                     json={"parameters":kwargs}
#                 )
#                 response.raise_for_status()
#                 result = response.json()

#                 if result.get("error"):
#                     raise Exception(f"Tool execution error: {result['error']}")
                    
#                 return result["result"]

#         except httpx.HTTPError as e:
#             raise Exception(f"HTTP error calling tool service: {str(e)}")
        
#         except Exception as e:
#             raise Exception(f"Error executing tool '{tool_name} : {str(e)}")

#     proxy_tool.__name__ = tool_name
#     proxy_tool.__doc__ = description or f"Proxy tool for {tool_name}"
    
#     return proxy_tool

import textwrap

def create_proxy_tool(tool_name: str, service_url: str, description: str, parameters: Dict[str, str]):
    """Dynamically created proxy tool with explicit parameters"""
    params_signature = ", ".join(parameters.keys())
    params_dict = ", ".join(f"'{k}': {k}" for k in parameters.keys())

    fn_code = f"""
    async def proxy_tool({params_signature}):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "{service_url}/tools/{tool_name}",
                    json={{"parameters": {{{params_dict}}}}}
                )
                response.raise_for_status()
                result = response.json()

                if result.get("error"):
                    raise Exception(f"Tool execution error: {{result['error']}}")

                return result["result"]

        except httpx.HTTPError as e:
            raise Exception(f"HTTP error calling tool service: {{str(e)}}")

        except Exception as e:
            raise Exception(f"Error executing tool '{tool_name}': {{str(e)}}")
    """

    local_vars = {}
    exec(textwrap.dedent(fn_code), globals(), local_vars)
    proxy_tool = local_vars['proxy_tool']

    proxy_tool.__name__ = tool_name
    proxy_tool.__doc__ = description or f"Proxy tool for {tool_name}"

    return proxy_tool



@app.post("/admin/register-tool")
async def register_tool(request: ToolRegistrationRequest):
    """Register a new tool with the MCP server - ONE TIME REGISTRATION"""
    tool_name = request.tool_name

    if tool_name in registered_tools:
        return {
            "status": "already exists",
            "message": f"Tool '{tool_name}' is already registered",
            "tool" : tool_name
        }
    
    try:
        proxy_function = create_proxy_tool(
            tool_name,
            request.tool_service_url,
            request.description,        
            request.parameters
        )

        decorated_tool = mcp.tool(tool_name)(proxy_function)

        registered_tools[tool_name] ={
            "service_url" : request.tool_service_url,
            "description": request.description,
            "parameters": request.parameters,
            "function": decorated_tool
        }

        return {
            "status": "success",
            "message": f"Tool '{tool_name}' registered successfully",
            "tool": tool_name,
            "total_tools": len(registered_tools)
        }

        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register tool: {str(e)}")

    

@app.get("/admin/tools")
async def list_registered_tools():
    """List all currently registered tools"""
    return {
        "registered_tools":{
            name: {
                "service_url": info["service_url"],
                "description": info["description"],
                "parameters": info["parameters"]
            }
            for name, info in registered_tools.items()
        },
        "tool_count": len(registered_tools)
    }


@app.delete("/admin/tools/{tool_name}")
async def unregister_tool(tool_name:str):
    """Remove a tool from tracking (Note: Cannot remove from MCP once registered)"""
    if tool_name not in registered_tools:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name} not found'")

    del registered_tools[tool_name]

    return {
        "status": "success",
        "message": f"Tool '{tool_name}' removed from tracking",
        "note": "Tool may still be available in MCP until server restart"
    }


@app.post("/admin/discover-tools")
async def discover_and_register_tools():
    """Discover tools from the tool service and register them"""
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{TOOL_SERVICE_URL}/tools")
            response.raise_for_status()
            available_tools = response.json()
        
        registered = []
        skipped = []
        failed = []
        
        for tool_name, tool_info in available_tools.items():
            if tool_name in registered_tools:
                skipped.append(tool_name)
                continue
            
            try:
                # Create registration request
                reg_request = ToolRegistrationRequest(
                    tool_name=tool_name,
                    tool_service_url=TOOL_SERVICE_URL,
                    description=tool_info.get("description", ""),
                    parameters=tool_info.get("parameters", {})
                )
                
                # Register the tool
                result = await register_tool(reg_request)
                if result["status"] == "success":
                    registered.append(tool_name)
                else:
                    failed.append(f"{tool_name}: {result['message']}")
                    
            except Exception as e:
                failed.append(f"{tool_name}: {str(e)}")
        
        return {
            "status": "completed",
            "registered": registered,
            "skipped": skipped,
            "failed": failed,
            "summary": f"Registered {len(registered)}, Skipped {len(skipped)}, Failed {len(failed)}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")

# =============================================================================
# MCP TOOL FOR SELF-MANAGEMENT
# =============================================================================

@mcp.tool()
async def register_remote_tool(tool_name: str, service_url: str, description: str = "") -> str:
    """MCP tool to register other tools dynamically"""
    
    request = ToolRegistrationRequest(
        tool_name=tool_name,
        tool_service_url=service_url,
        description=description
    )
    
    try:
        result = await register_tool(request)
        return f"Registration result: {result['message']}"
    except Exception as e:
        return f"Registration failed: {str(e)}"

@mcp.tool()
async def list_available_tools() -> Dict[str, Any]:
    """MCP tool to list all registered tools"""
    return {
        "tools": list(registered_tools.keys()),
        "count": len(registered_tools),
        "details": {
            name: info["description"] 
            for name, info in registered_tools.items()
        }
    }

# =============================================================================
# STARTUP AND HEALTH
# =============================================================================

# @app.on_event("startup")
# async def startup_event():
#     """Auto-discover and register tools on startup"""
#     print("MCP Server starting up...")
    
#     # Try to auto-discover tools if TOOL_SERVICE_URL is set
#     if TOOL_SERVICE_URL and TOOL_SERVICE_URL != "https://your-tool-service.run.app":
#         try:
#             await asyncio.sleep(2)  # Give tool service time to start
#             result = await discover_and_register_tools()
#             print(f"Startup discovery: {result['summary']}")
#         except Exception as e:
#             print(f"Startup discovery failed: {e}")

@app.get("/")
async def root():
    return {
        "message": "MCP Server is running",
        "registered_tools": len(registered_tools),
        "tool_service_url": TOOL_SERVICE_URL
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "mcp-server",
        "registered_tools": len(registered_tools)
    }

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8001)))


    

        