from fastapi import Depends
from services import OpenAIService, ChromaService
from models.dto import ConversationRequest
import json
from utils import call_tools_async
from langsmith import traceable
from crud.conversation import get_conversation
from help import deps

class ChatController:
    def __init__(self):
        pass

    @traceable
    @staticmethod
    async def get_data_for_rag(request_data: ConversationRequest, openai_service: OpenAIService = deps.get_openai_service(), chroma_service: ChromaService = deps.get_chroma_service()):
        conversation_id = request_data.conversation_id
        prompt = request_data.meta.content.parts[0]
        conversation = await get_conversation(conversation_id)
        history = [] 
        for item in conversation.get('history', []):
            history.extend(item)
        history = list(map(lambda x: {'role': x.get('role', ''), 'content': x.get('content', '')}, history))
        global_topic = conversation.get('global_topic', {'api': '', 'source': '', 'topic': '', 'type': ''})
        user_question = prompt.content
        keywords_text = openai_service.rewrite_and_extract_keyword(user_question, history, global_topic)
        keywords_dict = json.loads(keywords_text)

        features_keywords = await chroma_service.retrieve_keyword(keywords_dict, global_topic)

        
        context = await call_tools_async(features_keywords)

        return {
            "user_question": user_question,
            "conversation": {
                "conversation_id": conversation_id,
                "history": history  
            },
            "context": context,
            "global_topic": features_keywords['global_topic']
        }