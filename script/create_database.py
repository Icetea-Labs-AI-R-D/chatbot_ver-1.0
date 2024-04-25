import json
from langchain.docstore.document import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

# From dictionary to vectorDB items
with open('data/json/dictionary.json', 'r') as f:
    data_dict = json.load(f)

data_topic = []
data_content = []
    
for v, item in data_dict.items():
    if v == 'topic':
        for topic, item1 in item.items():
            for key, list_synonym in item1.items():
                for synonym in list_synonym:
                    dict_item = {
                        'page_content': synonym,
                        'metadata': {
                            'api': f'overview_{topic}',
                            'source': key,
                            'type': 'topic',
                            'topic': topic
                        }
                    }
                    data_topic.append(dict_item)
    else:
        for api, item2 in item.items():
            for key, list_synonym in item2.items():
                for synonym in list_synonym:
                    dict_item = {
                        'page_content': synonym,
                        'metadata': {
                            'api': api,
                            'source': key,
                            'type': 'content',
                            'topic': "_".join(api.split('_')[1:])
                        }
                    }
                    data_content.append(dict_item)
                    
docs_content = list(map(lambda x: Document(page_content=x['page_content'], metadata=x['metadata']), data_content))
docs_topic = list(map(lambda x: Document(page_content=x['page_content'], metadata=x['metadata']), data_topic))

persist_directory_content = './db/data_v1/content/'
persist_directory_topic = './db/data_v1/topic/'

# OpenAI embeddings
embedding = OpenAIEmbeddings()

vectordb_content = Chroma.from_documents(documents=docs_content,
                                 embedding=embedding,
                                 persist_directory=persist_directory_content)
vectordb_topic = Chroma.from_documents(documents=docs_topic,
                                 embedding=embedding,
                                 persist_directory=persist_directory_topic)
# Persist the db to disk
vectordb_content.persist()
vectordb_topic.persist()

vectordb_content = None
vectordb_topic = None