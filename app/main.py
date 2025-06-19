from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import httpx 
from typing import Optional
import os
from schemas import ProcessRequest,ProcessResponse, RouteDecision
from fastapi.encoders import jsonable_encoder


# config = {
#     "mcpServers": {
#         "local": {"command": "python", "args": ["local_server.py"]},
#         "remote": {"url": "https://url.com/mcp"},
#     }
# }
# mcp_client = Client(config)

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize services
# retriever = PineconeRetriever()
# rag_chain = RAGChain(retriever)

app = FastAPI(
    title="Credit Analyst RAG Service",
    description="LangChain processing endpoint for credit analysis",
    version="1.0.0"
)

# CORS Configuration (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_methods=["POST","GET"],
    allow_headers=["*"]
)

@app.post("/process")
async def process_request(request: ProcessRequest):
    """
    Process credit analysis request through RAG pipeline
    
    Parameters:
    - user_q: User's question (required)
    - faq_q: Matched FAQ question (optional)
    - intent: Detected intent (optional)
    - entity: Analyst level ('Associate', 'VP', etc.) (optional)
    - concept: Key concepts involved (optional)
    """
    try:
        route = "rag"

        #this will determine where to route 
        #route = await determine_routing(request)
        request_dict = jsonable_encoder(request)
        logging.info(f"Processing request: {request_dict}")
           
        if route == "rag":
            print("its rag")
            rag_response = await call_rag_system(request_dict)
        elif route == RouteDecision.MCP:
            print("its mcp")
            rag_response = await call_mcp_system(request_dict)
        else:
            rag_response = await generate_direct_response(request_dict)

        return {
            "source": "rag",
            "answer": rag_response["answer"],
            "sources": rag_response["sources"],
            "processed": False
        }
                
                
    except Exception as e:
        logging.error(f"Orchestration error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

async def call_rag_system(query: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://rag-service-1053292367606.us-central1.run.app/retrieve",
            json=query,
            timeout=10
        )

        return response.json()

async def call_mcp_system(query: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://0.0.0.0:8000/process",
            json=query,
            timeout=30.0
        )
        return {
            "source": "mcp",
            "response": response,
            "processed": True  # MCP typically returns final answers
        }


async def generate_direct_response(query: ProcessResponse):
    pass

# @app.get("/health")
# async def health_check():
#     """Service health check endpoint"""
#     try:
#         # Test Pinecone connection
#         test_docs = retriever.get_relevant_documents("test", k=1)
        
#         return {
#             "status": "healthy",
#             "pinecone_ready": bool(test_docs),
#             "service_version": "1.0.0"
#         }
#     except Exception as e:
#         raise HTTPException(
#             status_code=503,
#             detail=f"Service unhealthy: {str(e)}"
#         )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        log_level="info",
        reload=True
    )
    