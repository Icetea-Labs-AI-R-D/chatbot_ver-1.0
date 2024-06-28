from fastapi import Depends
import openai
from services import OpenAIService, ChromaService
import json
from utils import call_tools_async
from langsmith import traceable
from database.session import MongoManager
from models.dto import ConversationRequest
from openai import AsyncOpenAI
from dotenv import load_dotenv
load_dotenv('.env')

class ChatController:
    openai_service: OpenAIService
    chroma_service: ChromaService
    db: MongoManager

    def __init__(self) -> None:
        self.openai_service = OpenAIService()
        self.chroma_service = ChromaService()
        self.db = MongoManager()

    @traceable
    async def get_data_for_rag(
        self,
        request_data: ConversationRequest,
        openai_client: AsyncOpenAI,
    ):
        conversation_id = request_data.conversation_id
        prompt = request_data.content
        new_conversation = 0
        conversation = await self.db.get_conversation(conversation_id)
        if conversation == {}:
            new_conversation = 1
        global_topic = conversation.get(
            "global_topic", {"api": "", "source": "", "topic": "", "type": ""}
        )
        raw_history = list(
            map(
                lambda x: {
                    "content_user": x.get("content_user", ""),
                    "content_assistant": x.get("content_assistant", ""),
                    "context": x.get("context", ""),
                    "features_keywords": x.get("features_keywords", {}),
                    "suggestion": x.get("suggestion", []),
                },
                conversation.get("history", []),
            )
        )
        selected_suggestions = conversation.get("selected_suggestions", [])
        history = []
        for _ in raw_history:
            history.extend(
                [
                    {"role": "user", "content": _["content_user"]},
                    {"role": "assistant", "content": _["content_assistant"]},
                ]
            )
        user_question = prompt.lower()
        context = "[]"
        features_keywords = {}
        suggestions = []
        rag = True
        if raw_history:
            suggestions = raw_history[-1].get("suggestion", [])
        suggestion = {}
        for s in suggestions:
            if s.get("question", "") == prompt:
                suggestion = s
                selected_suggestions.append(suggestion)
                break
        if request_data.suggested == 0 or not raw_history or raw_history[-1].get("context", "") == "" or not suggestion.get('is_related', False):
            keywords_text = await self.openai_service.rewrite_and_extract_keyword(
                user_question, history, global_topic, openai_client
            )
            keywords_dict = json.loads(keywords_text)
            features_keywords = await self.chroma_service.retrieve_keyword(
                keywords_dict, global_topic, user_message=user_question, openai_client=openai_client
            )
            if  global_topic != features_keywords.get("global_topic", {}) and global_topic.get("api", "") != "overview_list_ido_upcoming":
                selected_suggestions = []
                
            if features_keywords['global_topic'].get('api', "") != "":
                context = await call_tools_async(features_keywords)
        else:
            rag = False
            context = raw_history[-1].get("context", "")
            features_keywords = raw_history[-1].get("features_keywords", {})

        return {
            "user_question": user_question,
            "conversation": {"conversation_id": conversation_id, "history": history},
            "context": context,
            "global_topic": features_keywords.get(
                "global_topic", {"api": "", "source": "", "topic": "", "type": ""}
            ),
            "features_keywords": features_keywords,
            "new_conversation": new_conversation,
            "selected_suggestions": selected_suggestions,
            "rag": rag,
        }
    
    async def new_conversation(self, conversation_id: str) -> None:
        await self.db.close_conversation(conversation_id)
        await self.db.new_conversation(conversation_id)