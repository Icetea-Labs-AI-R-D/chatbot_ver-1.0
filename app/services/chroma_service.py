from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import os
import asyncio
from langsmith import traceable

load_dotenv()
class ChromaService:
    persist_directory: str
    embedding: OpenAIEmbeddings
    vectordb_topic: Chroma
    vectordb_content: Chroma
    vectordb_docs: Chroma
    def __init__(self) -> None:
        self.persist_directory = os.getenv('PERSISTENCE_PATH')
        self.embedding = OpenAIEmbeddings(api_key=os.getenv('OPENAI_API_KEY3'))
        self.vectordb_topic = Chroma(
            persist_directory=f'{self.persist_directory}/topic/',
            embedding_function=self.embedding)
        self.vectordb_content = Chroma(
            persist_directory=f'{self.persist_directory}/content/',
            embedding_function=self.embedding)
        self.vectordb_docs = Chroma(
            persist_directory=f'{self.persist_directory}/docs/',
            embedding_function=self.embedding)
        
        
    async def async_similarity_search(self, k: str = "", _filter: dict = {}):
        return self.vectordb_content.similarity_search(
                k,
                k=3,
                filter=_filter
            )
        
    async def async_similarity_search_with_scores(self, k: str = "", index: int = 0):
        return (self.vectordb_docs.similarity_search_with_score(
                k.lower(),
                k=1
            )[0], index)

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
            retrieved_topics = list(filter(lambda x: x[0][0].metadata['type'] == 'topic', retrieved_topics))
            topics = sorted(retrieved_topics, key=lambda x: x[0][1], reverse=False)
            if len(topics) > 0:
                topic = list(map(lambda x: x, topics))[0]
                keywords = list(filter(lambda x: x[1] != topic[1], keywords))
                topic = topic[0][0].metadata
                global_topic = topic
            _filter = {
                'topic': global_topic.get('topic', '')
            }
            keywords = list(map(lambda x: x[0], keywords))
            retrieved_tasks = [self.async_similarity_search(k, _filter) for k in keywords]
            group_contents = await asyncio.gather(*retrieved_tasks)
            for task in group_contents:
                contents.extend(task)
            contents = list(map(lambda x: x.metadata, contents))
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