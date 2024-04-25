from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import os
import asyncio
class ChromaService:
    persist_directory: str
    embedding: OpenAIEmbeddings
    vectordb_topic: Chroma
    vectordb_content: Chroma
    def __init__(self) -> None:
        self._load_config()
        # OpenAI embeddings
        self.embedding = OpenAIEmbeddings()
        self.vectordb_topic = Chroma(
            persist_directory=f'{self.persist_directory}/topic/',
            embedding_function=self.embedding)

        self.vectordb_content = Chroma(
            persist_directory=f'{self.persist_directory}/content/',
            embedding_function=self.embedding)
        
    def _load_config(self) -> None:
        self.persist_directory = os.getenv('PERSISTENCE_PATH')
        
    async def async_similarity_search(self, k: str = "", topic: str = ""):
        return self.vectordb_content.similarity_search(
                k,
                k=3,
                filter={
                    'topic': topic,
                    }
            )
        
    async def async_similarity_search_with_scores(self, k: str = "", index: int = 0):
        return (self.vectordb_topic.similarity_search_with_score(
                k.lower(),
                k=1
            )[0], index)

    async def _retrieve_keyword(self, keyword: dict) -> dict:
        try:     
            keyword = keyword['keywords']
            topics = []
            contents = []
            retrieved_topics = []
            retrieved_tasks = []
            keywords = [(k, index) for index, k in enumerate(keyword)]
            retrieved_tasks = [self.async_similarity_search_with_scores(k, index) for index, k in enumerate(keyword)]
            retrieved_topics = await asyncio.gather(*retrieved_tasks)
            topics = sorted(retrieved_topics, key=lambda x: x[0][1], reverse=False)
            topic = topics[0]
            keywords = list(filter(lambda x: x[1] != topic[1], keywords))
            keywords = list(map(lambda x: x[0], keywords))
            topic = topic[0][0].metadata
            retrieved_tasks = [self.async_similarity_search(k, topic['topic']) for k in keywords]
            group_contents = await asyncio.gather(*retrieved_tasks)
            for task in group_contents:
                contents.extend(task)
            contents = list(map(lambda x: x.metadata, contents))
            return {
                "topic": topic,
                "content": contents
            }
        except Exception as e:
            print(e)
            return {
                "topic": "",
                "content": []
            }