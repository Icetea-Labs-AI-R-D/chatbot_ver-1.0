import json
from langchain.docstore.document import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv
import requests

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

docs_topic = list(filter(lambda x: x.metadata['topic'] != 'ido_upcoming', docs_topic))

persist_directory_content = './db/data_v2/content/'
persist_directory_topic = './db/data_v2/topic/'
persist_directory_docs = './db/data_v2/docs/'

docs = docs_content + docs_topic

# OpenAI embeddings
embedding = OpenAIEmbeddings()

vectordb_docs = Chroma.from_documents(documents=docs,
                                 embedding=embedding,
                                 persist_directory=persist_directory_docs)
vectordb_content = Chroma.from_documents(documents=docs_content,
                                 embedding=embedding,
                                 persist_directory=persist_directory_content)
vectordb_topic = Chroma.from_documents(documents=docs_topic,
                                 embedding=embedding,
                                 persist_directory=persist_directory_topic)
# Persist the db to disk
vectordb_content.persist()
vectordb_topic.persist()
vectordb_docs.persist()
vectordb_docs = None
vectordb_content = None
vectordb_topic = None

def get_upcoming_IDO():
    url = "https://ido.gamefi.org/api/v3/pools/upcoming"
    headers = {
        "Accept": "application/json",
    }
    reponse = requests.get(url, headers).json()
    list_project_name = []
    data = reponse['data']
    for item in data:
        list_project_name.append(
            {
               'name': item['name'],
               'slug': item['slug']
            }
        )
    overview = {
        "number_of_upcoming_IDO": len(list_project_name),
        "list_project": list_project_name
    }
    return overview

def update_vector_topic(vector_topic):
    # Remove old ido_upcoming topic from vector_topic
    list_old_ids = list(filter(lambda x: x.startswith('ido_upcoming') ,vector_topic._collection.get()['ids']))
    print(list_old_ids)
    if not list_old_ids : list_old_ids = ['']
    vector_topic._collection.delete(list_old_ids)
    
    # Get new ido_upcoming topic
    new_data = get_upcoming_IDO()
    
    # Update new ido_upcoming topic to vector_topic
    new_topic_ido_upcoming = new_data['list_project']
    new_topic = []
    for doc in new_topic_ido_upcoming:
        document = Document(page_content=doc['name'], metadata={'api': 'overview_ido_upcoming', 'source': doc['slug'], 'type': 'topic', 'topic': 'ido_upcoming'})
        new_topic.append(document)
    print(new_topic)
    vector_topic.add_documents(
        documents=new_topic, 
        ids=[f'ido_upcoming_{i+1}' for i in range(len(new_topic_ido_upcoming))],
    )
    vector_topic.persist()

vectordb_topic = Chroma(persist_directory=persist_directory_topic,
                   embedding_function=embedding)
vectordb_docs = Chroma(persist_directory=persist_directory_docs,
                   embedding_function=embedding)

update_vector_topic(vectordb_topic)
update_vector_topic(vectordb_docs)