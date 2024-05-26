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
        prompt = request_data.content
        new_conversation = 0
        conversation = await self.db.get_conversation(conversation_id)
        rag = conversation.get('rag', 0)
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
                },
                conversation.get("history", []),
            )
        )
        history = []
        for _ in raw_history:
            history.extend(
                [
                    {"role": "user", "content": _["content_user"]},
                    {"role": "assistant", "content": _["content_assistant"]},
                ]
            )
        user_question = prompt
        context = "[]"
        features_keywords = {}
        if request_data.suggested == 0 or not raw_history or raw_history[-1].get("context", "") == "" or rag >= 2:
            rag = 0
            keywords_text = await self.openai_service.rewrite_and_extract_keyword(
                user_question, history, global_topic, openai_client
            )
            keywords_dict = json.loads(keywords_text)
            features_keywords = await self.chroma_service.retrieve_keyword(
                keywords_dict, global_topic
            )

            context = await call_tools_async(features_keywords)
        else:
            context = raw_history[-1].get("context", "")
            features_keywords = raw_history[-1].get("features_keywords", {})
            rag = rag + 1

        return {
            "user_question": user_question,
            "conversation": {"conversation_id": conversation_id, "history": history},
            "context": context,
            "global_topic": features_keywords.get(
                "global_topic", {"api": "", "source": "", "topic": "", "type": ""}
            ),
            "features_keywords": features_keywords,
            "new_conversation": new_conversation,
            "rag": rag,
        }
    
    async def new_conversation(self, conversation_id: str) -> None:
        await self.db.close_conversation(conversation_id)