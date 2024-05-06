from fastapi import Request
from services import OpenAIService, ChromaService, ConversationService
from models.dto import ConversationRequest
import json
from utils import call_tools_async

class ChatController:
    openai_service: OpenAIService
    chroma_service: ChromaService
    conversation_service: ConversationService

    def __init__(self):
        self.openai_service = OpenAIService()
        self.chroma_service = ChromaService()
        self.conversation_service = ConversationService()

    async def _qa_conversation(self, request_data: ConversationRequest):
        conversation_id = request_data.conversation_id
        prompt = request_data.meta.content.parts[0]
        history = self.conversation_service.get_conversation(conversation_id)
        history = list(map(lambda x: {'role': x['role'], 'content': x['content']}, history))
        user_question = prompt.content
        keywords_text = self.openai_service._rewrite_and_extract_keyword(user_question, history)
        keywords_dict = json.loads(keywords_text)
        features_keywords = await self.chroma_service._retrieve_keyword(keywords_dict)
        
        context = await call_tools_async(features_keywords)

        return {
            "call": "ask_OpenAI_with_RAG",
            "user_question": user_question,
            "conversation": {
                "conversation_id": conversation_id, 
                "history": history    
            },
            "context": context,
            "rewrite_question": keywords_dict['rewritten_message'],
        }