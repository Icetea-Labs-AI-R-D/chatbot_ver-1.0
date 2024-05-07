from fastapi import Request
from services import OpenAIService, ChromaService, MongoService
from models.dto import ConversationRequest
import json
from utils import call_tools_async

class ChatController:
    openai_service: OpenAIService
    chroma_service: ChromaService
    mongo_service: MongoService

    def __init__(self):
        self.openai_service = OpenAIService()
        self.chroma_service = ChromaService()
        self.mongo_service = MongoService()

    async def _qa_conversation(self, request_data: ConversationRequest):
        conversation_id = request_data.conversation_id
        prompt = request_data.meta.content.parts[0]
        history = self.mongo_service.get_conversation(conversation_id)
        history = list(map(lambda x: {'role': x['role'], 'content': x['content'], 'previous_topic': x['previous_topic']}, history))
        user_question = prompt.content
        keywords_text = self.openai_service._rewrite_and_extract_keyword(user_question, history)
        keywords_dict = json.loads(keywords_text)
        if (len(history) > 2): 
            previous_topic = history[-1].get('previous_topic', {'api': '', 'source': '', 'topic': '', 'type': ''})
        else:
            previous_topic = {'api': '', 'source': '', 'topic': '', 'type': ''}
        features_keywords = await self.chroma_service._retrieve_keyword(keywords_dict, previous_topic)
        
        context = await call_tools_async(features_keywords)
        print(context)

        return {
            "user_question": user_question,
            "conversation": {
                "conversation_id": conversation_id, 
                "history": history    
            },
            "context": context,
            "rewrite_question": keywords_dict['rewritten_message'],
            "previous_topic": features_keywords['previous_topic']
        }