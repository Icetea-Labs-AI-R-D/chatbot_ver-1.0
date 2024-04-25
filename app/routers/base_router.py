from controllers.chat_controller import ChatController
from controllers.page_controller import PageController

class BaseRouter:
    chat_controller: ChatController
    page_controller: PageController

    def __init__(self) -> None:
        self.chat_controller = ChatController()
        self.page_controller = PageController()