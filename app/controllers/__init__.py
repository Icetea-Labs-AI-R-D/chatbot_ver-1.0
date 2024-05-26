from .chat_controller import ChatController
from .report_controller import ReportController

async def get_chat_controller() -> ChatController:
    return ChatController()

async def get_report_controller() -> ReportController:
    return ReportController()