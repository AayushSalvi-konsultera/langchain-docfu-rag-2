from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from rag.chains.rag_chains import RAGChain, RAGRequest
from rag.retrievers.pinecone import PineconeRetriever
import logging
import os
from rag.chains.context import ChainContext
from fastmcp import Client


config = {
    "mcpServers": {
        "local": {"command": "python", "args": ["local_server.py"]},
        "remote": {"url": "https://url.com/mcp"},
    }
}
mcp_client = Client(config)

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize services
retriever = PineconeRetriever()
rag_chain = RAGChain(retriever)

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
async def process_request(request: RAGRequest):
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
        logger.info(f"Processing request - Entity: {request.entity}, Intent: {request.intent}")
        logger.debug(f"Full request: {request.dict()}")
        
        rag_response = await rag_chain.invoke(request)


        logger.info("Successfully processed request")
        return {
            "answer": rag_response,
            "sources": [],  # default to empty list
        }
        
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/health")
async def health_check():
    """Service health check endpoint"""
    try:
        # Test Pinecone connection
        test_docs = retriever.get_relevant_documents("test", k=1)
        
        return {
            "status": "healthy",
            "pinecone_ready": bool(test_docs),
            "service_version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )
    