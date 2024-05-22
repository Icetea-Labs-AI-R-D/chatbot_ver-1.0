import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from app.utils.tools_async import embedding
class VectorDB:
    client = chromadb.PersistentClient
    embedding_function = OpenAIEmbeddingFunction
    def __init__(self) -> None:
        pass