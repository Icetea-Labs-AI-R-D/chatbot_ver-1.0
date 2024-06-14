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
import re
from fastapi import Depends
from services.openai_service import OpenAIService
import ast
load_dotenv(".env")


class ChromaService:
    persist_directory: str
    embedding_function: OpenAIEmbeddingFunction
    vectordb_topic: Any
    vectordb_content: Any
    vectordb_docs: Any
    openai_service: OpenAIService

    def __init__(self) -> None:
        client = chromadb.HttpClient()  
        self.openai_service = OpenAIService()
        # OpenAI embeddings
        self.embedding_function = OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY3")
        )
        self.vectordb_docs = client.get_or_create_collection(
            name="vector_docs",
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"},
        )
        self.vectordb_content = client.get_or_create_collection(
            name="vector_content",
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"},
        )
        self.vectordb_topic = client.get_or_create_collection(
            name="vector_topic",
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"},
        )

    async def async_similarity_search(self, k: str = "", _filter: dict = {}):
        result = self.vectordb_content.query(
            query_texts=[k], n_results=3, where=_filter
        )
        result = [
            {
                "page_content": result["documents"][0][i],
                "metadata": result["metadatas"][0][i],
            }
            for i in range(len(result["ids"][0]))
        ]
        return result

    async def async_similarity_search_with_scores(self, k: str = "", index: int = 0):
        result = self.vectordb_docs.query(query_texts=[k.lower()], n_results=1)
        result = [
            {
                "page_content": result["documents"][0][i],
                "metadata": result["metadatas"][0][i],
            }
            for i in range(len(result["ids"][0]))
        ]

        return (result[0], index)

    async def validate_change_topic(self, new_topic: dict, user_message: str, openai_client):
        pattern = r'[ \-_]+' 
        words = re.split(pattern=pattern, string=new_topic['metadata']['source'])
        words.extend(re.split(pattern=pattern, string=new_topic['page_content']))
        # print(user_message)
        # print(words)
        for word in words:
            if word in user_message.lower():
                return True
        response = await  self.openai_service.check_change_topic(topic_names = words, user_message=user_message, openai_client=openai_client)
        is_valid_change = ast.literal_eval(response)['is_mentioned']
        # print(response)
        # print("Is_valid_change", is_valid_change)
        return is_valid_change
    
    @traceable(run_type="retriever")
    async def retrieve_keyword(self, keyword: dict, global_topic: dict, user_message: str = "", openai_client = None) -> dict:
        try:
            topics = []
            contents = []
            retrieved_topics = []
            retrieved_tasks = []
            keyword = keyword.get("keywords", [])
            
            if len(keyword) == 0 and user_message != "":
                keyword = [user_message]
            
            keywords = [(k, index) for index, k in enumerate(keyword)]

            retrieved_tasks = [
                self.async_similarity_search_with_scores(k, index)
                for k, index in keywords
            ]

            retrieved_topics = await asyncio.gather(*retrieved_tasks)
            retrieved_topics = list(
                filter(lambda x: x[0]["metadata"]["type"] == "topic", retrieved_topics)
            )

            topics = retrieved_topics
            
            if len(topics) > 0:
                topic = topics[0]
                
                keywords = list(filter(lambda x: x[1] != topic[1], keywords))
                if global_topic != topic:
                    check = await self.validate_change_topic(new_topic=topic[0], user_message=user_message, openai_client=openai_client)
                    if check == True or check == "True":
                        topic = topic[0]["metadata"]
                        global_topic = topic
                
                
                
            if  global_topic.get("topic", "") == 'end_phrase':
                return {
                    "topic": global_topic,
                    "content": contents,
                    "global_topic": global_topic,
                }
                
            _filter = {"topic": global_topic.get("topic", "")}
            keywords = list(map(lambda x: x[0], keywords))

            retrieved_tasks = [
                self.async_similarity_search(k, _filter) for k in keywords
            ]
            group_contents = await asyncio.gather(*retrieved_tasks)
            for task in group_contents:
                contents.extend(task)
            contents = list(map(lambda x: x["metadata"], contents))
            return {
                "topic": global_topic,
                "content": contents,
                "global_topic": global_topic,
            }
        except Exception as e:
            print(e)
            return {"topic": global_topic, "content": [], "global_topic": global_topic}
