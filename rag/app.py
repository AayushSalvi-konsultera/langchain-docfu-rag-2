from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import logging
import os
from dotenv import load_dotenv
load_dotenv()

from chains.rag_chains import RAGChain, RAGRequest
from retrievers.pinecone import PineconeRetriever
from chains.context import ChainContext

app = FastAPI()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

retriever = PineconeRetriever()
rag_chain = RAGChain(retriever)

@app.post("/retrieve")
async def retireve_documents(request:RAGRequest):
    try:
        
        rag_response = await rag_chain.invoke(request)


        logger.info("Successfully processed request")
        return {
            "answer": rag_response,
            "sources": [],  # default to empty list
        } 
    except Exception as e:
        logging.error(f"RAG Retrieval error: {str(e)}")
        raise HTTPException(status_code=500,detail= str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        log_level="info"    
        )
    