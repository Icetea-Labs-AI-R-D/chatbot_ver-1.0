import fastapi
from utils.google_sheet import create_new_report
from models.dto import ReportRequest
from database.session import MongoManager
from database import get_db


class ReportController:
    db: MongoManager

    def __init__(self) -> None:
        self.db = MongoManager()

    async def generate_report(self, request: ReportRequest):
        conversation_id = request.conversation_id
        content = request.content
        conversation = await self.db.get_report_conversation(conversation_id)
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
        if not raw_history:
            raw_history = [{}]
        report = [
            conversation_id,
            content,
            str(global_topic),
            str(raw_history[-1].get("content_user", "")),
            str(raw_history[-1].get("content_assistant", "")),
            str(raw_history[-1].get("context", "")),
            str(raw_history[-1].get("features_keywords", {})),
        ]
        await create_new_report(report)
