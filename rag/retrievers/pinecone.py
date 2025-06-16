from langchain_huggingface import HuggingFaceEmbeddings  # Updated import
from langchain_pinecone import PineconeVectorStore  # Recommended new import
from pinecone import Pinecone
import os

class PineconeRetriever:
    def __init__(self):
        # Initialize Pinecone client (new SDK)
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        
        # Initialize embeddings (new package)
        self.embedding = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize vectorstore (recommended new way)
        self.vectorstore = PineconeVectorStore(
            index_name=os.getenv("PINECONE_INDEX_NAME", "new-credit-analyst-rag-v2"),
            embedding=self.embedding,
            text_key="text"  # Must match your metadata field
        )

    def get_relevant_documents(self, query: str, k: int = 3):
        """Retrieve top k most relevant documents"""
        return self.vectorstore.similarity_search(query, k=k)

# class PineconeRetriever:
#     def __init__(self):
#         load_dotenv()
        
#         # Initialize Pinecone client
#         print(os.getenv("PINECONE_API_KEY"))
#         self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        
        
#         self.index_name = "new-credit-analyst-rag-v2"
#         self.embedding = HuggingFaceEmbeddings(
#             model_name="all-MiniLM-L6-v2",
#             model_kwargs={'device': 'cpu'},
#             encode_kwargs={'normalize_embeddings': True}
#         )
        
#         # Load vectorstore from existing index using LangChain's integration
#         self.vectorstore = LangchainPinecone.from_existing_index(
#             index_name=self.index_name,
#             embedding=self.embedding,
#             namespace=os.getenv("PINECONE_NAMESPACE", "default")
#         )

#     def get_relevant_documents(self, query: str, k: int = 3):
#         """Retrieve top k most relevant documents"""
#         return self.vectorstore.similarity_search(query, k=k)
