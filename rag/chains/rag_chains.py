from llm.gemini import GeminiClient
from typing import List
from langchain_core.documents import Document
from pydantic import BaseModel
from typing import Optional, List


class RAGRequest(BaseModel):
    user_q: str
    faq_q: Optional[str] = None
    intent: Optional[str] = None
    entity: Optional[str] = None
    concept: Optional[List[str]] = None
class RAGChain:
    def __init__(self, retriever):
        self.retriever = retriever
        self.llm = GeminiClient()

    def _format_docs(self, docs: List[Document]) -> str:
        """Format retrieved documents for context"""
        return "\n\n".join(
            f"🔹 {doc.page_content}\n(Source: {doc.metadata.get('source', 'unknown')})"
            for doc in docs
        )

    def _build_prompt(self, request: RAGRequest, context: str) -> str:
        """Construct the professional analyst prompt"""
        return f"""
        You are a {request.entity}-level credit analyst. 
        
        The user has asked: {request.user_q}
        
        According to our knowledge base:
        - Most relevant FAQ match: {request.faq_q if request.faq_q else "No direct FAQ match"}
        - Key concepts involved: {request.concept if request.concept else "General inquiry"}
        - Detected intent: {request.intent if request.intent else "Not specified"}
        
        Context from documents:
        {context}
        
        Guidelines:
        1. Answer as a professional {request.entity}-level analyst
        2. If the context doesn't contain the answer, say: 
           "I don't have sufficient information to answer this authoritatively"
        3. Never guess - only use what's in the provided context
        4. When possible, reference the source documents
        
        Structured Analysis:
        """

    async def invoke(self, request: RAGRequest):
        """Execute full RAG pipeline with enhanced prompt"""
        try:
            # 1. Retrieve relevant documents
            search_query = f"{request.user_q} {request.faq_q} {request.concept}"
            docs = self.retriever.get_relevant_documents(search_query, k=3)
            
            # 2. Format context
            formatted_context = self._format_docs(docs)
            
            # 3. Generate professional prompt
            prompt = self._build_prompt(request, formatted_context)
            
            # 4. Get LLM response
            return await self.llm.generate(prompt)
            
        except Exception as e:
            return f"Analysis error: {str(e)}"