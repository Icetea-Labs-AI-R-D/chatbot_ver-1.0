from chromadb.config import Settings
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import chromadb
import uuid
import os
from dotenv import load_dotenv
import requests
import json
load_dotenv('.env')

def add_data_to_vector(data, vector):
    vector.add(
        documents=[item['page_content'] for item in data],
        metadatas=[item['metadata'] for item in data],
        ids=[str(uuid.uuid4()) for _ in range(len(data))],
    )
  

def add_full_data_to_vector(data, vector):
    for i in range(0, len(data), 1000):
        vector.add(
            documents=[item['page_content'] for item in data[i:i+1000]],
            metadatas=[item['metadata'] for item in data[i:i+1000]],
            ids=[str(uuid.uuid4()) for _ in range(len(data[i:i+1000]))],
        )
        
    print(f"Added {len(data)} items to vector {vector.name}")
    print(f"Total items in vector {vector.name}: {vector.count()}")
 
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

def update_topic_vector_db(vector_db):
    print(f"Total items in vector {vector_db.name} before update: {vector_db.count()}")
    # Remove old ido_upcoming topic from vector_db
    list_old_ids = list(filter(lambda x: x.startswith('ido_upcoming') ,vector_db.get()['ids']))
    # print(list_old_ids)
    if not list_old_ids : list_old_ids = ['']
    vector_db.delete(ids=list_old_ids)
    
    # Get new ido_upcoming topic
    new_data = get_upcoming_IDO()
    
    # Update new ido_upcoming topic to vector_db
    new_topic_ido_upcoming = new_data['list_project']
    new_topic = []
    for doc in new_topic_ido_upcoming:
        # document = Document(page_content=doc['name'], metadata={'api': 'overview_ido_upcoming', 'source': doc['slug'], 'type': 'topic', 'topic': 'ido_upcoming'})
        item = {
            'page_content': doc['name'],
            'metadata': {'api': 'overview_ido_upcoming', 'source': doc['slug'], 'type': 'topic', 'topic': 'ido_upcoming'}
        }
        new_topic.append(item)
        item = {
            'page_content': doc['slug'],
            'metadata': {'api': 'overview_ido_upcoming', 'source': doc['slug'], 'type': 'topic', 'topic': 'ido_upcoming'}
        }
        new_topic.append(item)
    # print(new_topic)
    vector_db.add(
        documents=[item['page_content'] for item in new_topic], 
        ids=[f'ido_upcoming_{i+1}' for i in range(len(new_topic))],
        metadatas=[item['metadata'] for item in new_topic]
    )
    
    print(f"Added {len(new_topic)} items to vector {vector_db.name}")
    print(f"Total items in vector {vector_db.name} after update: {vector_db.count()}")

            
if __name__ == "__main__":

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
                    
    data_topic = list(filter(lambda x: x['metadata']['topic'] != 'ido_upcoming', data_topic))
    data_all = data_content + data_topic
                    
    
    embedding_function = OpenAIEmbeddingFunction(api_key=os.getenv('OPENAI_API_KEY1'))
    client = chromadb.HttpClient()
    vector_docs = client.get_or_create_collection(
        name="vector_docs", embedding_function=embedding_function, metadata={"hnsw:space": "cosine"})
    vector_content = client.get_or_create_collection(
        name="vector_content", embedding_function=embedding_function, metadata={"hnsw:space": "cosine"})
    vector_topic = client.get_or_create_collection(
        name="vector_topic", embedding_function=embedding_function, metadata={"hnsw:space": "cosine"})

    add_full_data_to_vector(data_all, vector_docs)
    add_full_data_to_vector(data_content, vector_content)
    add_full_data_to_vector(data_topic, vector_topic)
    
    update_topic_vector_db(vector_topic)
    update_topic_vector_db(vector_docs)
    
    # vector_docs.add(
    #     documents=['thank you', "thank you for your information"],
    #     metadatas=[
    #         {'api': '', 'source': '', 'type': 'topic', 'topic': 'end_phrase'},
    #         {'api': '', 'source': '', 'type': 'topic', 'topic': 'end_phrase'},
    #     ],
    #     ids=["end_phrase_1", "end_phrase_2"],
    # )