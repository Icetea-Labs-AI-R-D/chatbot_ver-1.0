from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import os
import asyncio
from langsmith import traceable
from dotenv import load_dotenv
from typing import Any
load_dotenv('.env')

class ChromaService:
    persist_directory: str
    embedding_function: OpenAIEmbeddingFunction
    vectordb_topic: Any
    vectordb_content: Any
    vectordb_docs: Any
    def __init__(self) -> None:
        self.load_config()
        client = chromadb.HttpClient()
        
        # OpenAI embeddings
        self.embedding_function = OpenAIEmbeddingFunction(api_key=os.getenv('OPENAI_API_KEY'))
        self.vectordb_docs = client.get_or_create_collection(
            name="vector_docs", embedding_function=self.embedding_function, metadata={"hnsw:space": "cosine"})
        self.vectordb_content = client.get_or_create_collection(
            name="vector_content", embedding_function=self.embedding_function, metadata={"hnsw:space": "cosine"})
        self.vectordb_topic = client.get_or_create_collection(
            name="vector_topic", embedding_function=self.embedding_function, metadata={"hnsw:space": "cosine"})

        
        
    async def async_similarity_search(self, k: str = "", _filter: dict = {}):
        result =  self.vectordb_content.query(
                query_texts=[
                    k
                ],
                n_results=3,
                where=_filter
            )
        result = [{'page_content': result['documents'][0][i], 'metadata': result['metadatas'][0][i]} for i in range(len(result['ids'][0]))]
        return result
        
    async def async_similarity_search_with_scores(self, k: str = "", index: int = 0):
        result = self.vectordb_docs.query(
                query_texts=[
                    k.lower()
                ],
                n_results=1
            )
        
        result = [{'page_content': result['documents'][0][i], 'metadata': result['metadatas'][0][i]} for i in range(len(result['ids'][0]))]
        
        return (result[0], index)

    @traceable(run_type="retriever")
    async def retrieve_keyword(self, keyword: dict, global_topic:dict) -> dict:
        try:     

            topics = []
            contents = []
            retrieved_topics = []
            retrieved_tasks = []
            keyword = keyword['keywords']
            keywords = [(k, index) for index, k in enumerate(keyword)]
            retrieved_tasks = [self.async_similarity_search_with_scores(k, index) for index, k in enumerate(keyword)]
            
            retrieved_topics = await asyncio.gather(*retrieved_tasks)
            
            retrieved_topics = list(filter(lambda x: x[0]['metadata']['type'] == 'topic', retrieved_topics))
            
            # topics = sorted(retrieved_topics, key=lambda x: x[0][1], reverse=False)
            topics = retrieved_topics
            if len(topics) > 0:
                topic = topics[0]
                
                keywords = list(filter(lambda x: x[1] != topic[1], keywords))
                topic = topic[0]['metadata']
                global_topic = topic
            _filter = {
                'topic': global_topic.get('topic', '')
            }
            keywords = list(map(lambda x: x[0], keywords))
            
            retrieved_tasks = [self.async_similarity_search(k, _filter) for k in keywords]
            group_contents = await asyncio.gather(*retrieved_tasks)
            for task in group_contents:
                contents.extend(task)
            contents = list(map(lambda x: x['metadata'], contents))
            return {
                "topic": global_topic,
                "content": contents,
                "global_topic": global_topic
            }
        except Exception as e:
            print(e)
            return {
                "topic": "",
                "content": [],
                "global_topic": global_topic
            }