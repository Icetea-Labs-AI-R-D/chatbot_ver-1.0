from fastapi import Depends
import openai
from services import OpenAIService, ChromaService
import json
from utils import call_tools_async
from langsmith import traceable
from database.session import MongoManager
from models.dto import ConversationRequest
from openai import AsyncOpenAI

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
        prompt = request_data.meta.content.parts[0]
        conversation = await self.db.get_conversation(conversation_id)
        history = []
        for item in conversation.get("history", []):
            history.extend(item)
        history = list(
            map(
                lambda x: {"role": x.get("role", ""), "content": x.get("content", "")},
                history,
            )
        )
        global_topic = conversation.get(
            "global_topic", {"api": "", "source": "", "topic": "", "type": ""}
        )
        user_question = prompt.content
        keywords_text = await self.openai_service.rewrite_and_extract_keyword(
            user_question, history, global_topic, openai_client
        )
        keywords_dict = json.loads(keywords_text)

        features_keywords = await self.chroma_service.retrieve_keyword(
            keywords_dict, global_topic
        )

        context = await call_tools_async(features_keywords)

        return {
            "user_question": user_question,
            "conversation": {"conversation_id": conversation_id, "history": history},
            "context": context,
            "global_topic": features_keywords["global_topic"],
            "features_keywords": features_keywords,
        }
