from .chat_controller import ChatController

async def get_chat_controller() -> ChatController:
    return ChatController()