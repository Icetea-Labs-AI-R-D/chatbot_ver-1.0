from openai import OpenAI
import os
from time import sleep
from .chroma_service import ChromaService
from .conversation_service import ConversationService

global_topic = {'api': 'overview_gamehub', 'source': '', 'topic': 'gamehub', 'type': 'topic'}

class OpenAIService:
    openai_client: OpenAI
    chroma_service: ChromaService
    conversation_service: ConversationService

    def __init__(self) -> None:
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.chroma_service = ChromaService()
        self.conversation_service = ConversationService()

    def _rewrite_and_extract_keyword(self, message: str, conversation: list = []):
        fe = []

        fe1 = self.chroma_service.vectordb_topic.similarity_search_with_score(
                    message.lower(),
                    k=3
                )   
        fe.extend(fe1) 
        fe = list(set([k[0].metadata['source'] for k in fe]))
        global global_topic
        fe.append(global_topic['source'])
        
        conversation = conversation[-2:]
        
        system_prompt = f'''
        You are a helpful agent designed to paraphrase the user message into a complete sentence.
        
        You are going to rewrite message about GameFi games, users have the tendency to ask about the game's attributes, components, or features. 
        There are some topic that the user can ask about, such as:
        {fe}
        ALWAYS INCLUDE MAIN TOPIC IN THE RESPONSE.
        These topics are at the same level of importance. You should be able to detect if the User change the topic that they want to get information.
        Keywords should be a list of words that are important in the user's message. They can be nouns, verbs, adjectives, etc.
        
        Give the response in JSON format contains 2 keys: "rewritten_message" and "keywords"
        
        #### Example ####
        Here are some example of the conversation between user and assistant:
        
        Example 1:
        History:
        - user: "Can you tell me about Mobox?"
        - assistant: "MOBOX is a community-driven GameFi platform empowering users by rewarding them for their engagement and enjoyment. By using innovative tokenomics ($MBOX allocation), utilizing finance and games. Whilst also combining the best of DeFi and NFTs to create a truly unique and everlasting FREE TO PLAY, PLAY TO EARN ECOSYSTEM."
        Current user's message: 
        - user: "Who are the backers of this project?"
        
        Think step by step: 
        Thought 1: The user is asking about a game name "Mobox". -> Include "Mobox" in response.
        Thought 2:  The user is asking about "backers" of "Mobox" -> Include "backers" and "Mobox" in keywords
        
        Then your response would be: 
        {{
            "rewritten_message": "Who are the backers of Mobox?",
            "keywords": ["Mobox", "backers"]
        }} 

        Example 2:
        History:
        - user: "Can you tell me about Mobox?"
        - assistant: "MOBOX is a community-driven GameFi platform empowering users by rewarding them for their engagement and enjoyment. By using innovative tokenomics ($MBOX allocation), utilizing finance and games. Whilst also combining the best of DeFi and NFTs to create a truly unique and everlasting FREE TO PLAY, PLAY TO EARN ECOSYSTEM."
        Current user's message:
        - user: "Can you tell me about the tokenomics of this project?"
        
        Think step by step:
        Thought 1: The user is asking about a game name "Mobox". -> Include "Mobox" in response.
        Thought 2: The user is asking about "tokenomics" of "Mobox" -> Include "tokenomics" and "Mobox" in keywords
        
        Then your response would be: 
        {{
            "rewritten_message": "Can you tell me about the tokenomics of Mobox?",
            "keywords": ["Mobox", "tokenomics"]
        }}
        
        When user asks about irrelevant topic, you can ignore the game's name in the response.
        
        Example 3:
        History:
        - user: "Can you tell me about Mobox?"
        - assistant: "MOBOX is a community-driven GameFi platform empowering users by rewarding them for their engagement and enjoyment. By using innovative tokenomics ($MBOX allocation), utilizing finance and games. Whilst also combining the best of DeFi and NFTs to create a truly unique and everlasting FREE TO PLAY, PLAY TO EARN ECOSYSTEM."
        Current user's message:
        - user: "What is the weather like today?"
        
        Think step by step:
        Thought 1: Mobox is mentioned in the history but not in the current user's message. -> Ignore Mobox in response.
        Thought 2: The user is asking about "weather today" -> Include "weather", "today" in keywords
        
        Then your response would be:
        {{
            "rewritten_message": "What is the weather like today?",
            "keywords": ["weather"]
        }}
        
        REMEMBER: Prioritize the game's name that appears in the current user's message.   
        '''
        
        nl = "\n"
        user_message = f"""
        History:
        {nl.join(f"- {c['role']}: {c['content']}" for c in conversation)}
        Current user's message: 
        - user: {message}
        """
        
        messages = [{"role": "system", "content": system_prompt}] + [{"role": "user", "content": user_message}]
        
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            temperature=0,
            response_format= {
                "type": "json_object"
            },
            messages=messages 
        )
        return str(response.choices[0].message.content)
    
    def _rewrite_and_extract_keyword_2(self, message: str, conversation: list = [], previous_response: dict = {}):
        
        system_prompt = '''
        You are a helpful agent designed to check the rewritten message and keywords from the user's message.
        Base on the conversation history to check whether the rewritten message is correct or not.
        There are cases that you should add the name of the game that is asked in the history into the rewritten message.
        
        Response in Json format contains two keys "rewritten_message" and "keywords"
        '''
    
        user_message = f"""
        User's message: {message}
        Previous rewrite agent response: {previous_response}
        
        """
        
        messages = [{"role": "system", "content": system_prompt}] + conversation + [{"role": "user", "content": user_message}]
        
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            temperature=0.1,
            response_format= {
                "type": "json_object"
            },
            messages=messages 
        )
        return str(response.choices[0].message.content)
    
    def _router(self, message: str, conversation: list = [], context: str = "[]"):
        conversation = conversation[-2:]
        
        system_prompt = f'''
        You are a helpful agent designed to look into user message and the provided context to check whether the user message can be answer with the provided context.
        
        If the context is not enough to answer the user message or empty, you should return "can_be_answered" as false.
        If the user message is irrelevant to the context, you should return "can_be_answered" as false. 
        
        Respond in a JSON string format with the following structure:
        {{
            "can_be_answered": true/false,
            "reason": "The reason why the user message can/can't be answered with the provided context."
        }}
        '''
        
        nl = "\n"
        
        user_message = f"""
        #### Context ####
        {context}
        #################   
        
        Current user's message: 
        - user: {message}
        """
        
        # History:
        # {nl.join(f"- {c['role']}: {c['content']}" for c in conversation)}
        
        messages = [{"role": "system", "content": system_prompt}] + conversation + [{"role": "user", "content": user_message}]
        
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            temperature=0,
            response_format= {
                "type": "json_object"
            },
            messages=messages 
        )
        return str(response.choices[0].message.content)
    
    def _handle_irrelevant_message(self, message: str, conversation: dict, context: str = "[]", rewrite_question: str = ""):
        history = conversation['history']
        history = history[-2:]
        
        system_prompt = f'''
        You are a helpful chatbot of GameFi.org.
        The user message that is given to you is already defined as irrelevant to what can be answered with information on GameFi.org.
        You are designed to answer irrelevant user messages .
        Here is the most relevant context:
        {context}
        
        If the context lacks of information that is asked in the user message, you should say "I dont have enough information to answer your question about {{paraphrased user' message}}".
        
        If the user message is irrelevant to the context, irrelevant to gameFI and GameFi.org, you should say "I am sorry, I can not answer your question about {{paraphrased user' message}}. I can provide information about game and Ido projects on GameFi.org.".
        Returns results in markdown format
        '''
        
        nl = "\n"
        
        user_message = f"""User's message: {message}"""
        # History:
        # {nl.join(f"- {c['role']}: {c['content']}" for c in conversation)}
        # Current user's message: 
        # - user: {message}
        
        
        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_message}]
        
        stream = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=messages,
            # temperature=0.2,
            stream=True,
        )
        
        answer = ""
        
        for chunk in stream:
            token = chunk.choices[0].delta.content
            if token is not None:
                answer += token
                print(token)
                yield token
        
        user = {
            "role": "user",
            "content": message, 
            "rewrite_question": rewrite_question
        }
        
        assistant = {
            "role": "assistant",
            "content": answer,
            "context": context 
        }
        
        history = conversation['history']
        history.append(user)
        history.append(assistant)
        
        n_conversation = {
            'conversation_id': conversation['conversation_id'],
            'history': history
        }
        self.conversation_service.add_conversation(n_conversation)
        
    def _ask_OpenAI_with_RAG(self, question: str, conversation: dict, context: str = "[]", rewrite_question: str = ""):
        history = conversation['history']
        system_message = f"""
        You are a friendly and informative chatbot, you can introduce yourself as 'GameFi Assistant'. 
        Your role is to help user to know more about games and IDO projects which are available on the GameFi platform. 
        Give information in a clear, concise and structured way.
        List of things should be listed with Bulleted list.
        
        Use the following pieces of information to response the user's message: 
        {context}
        -----------------   
        
        If the question does not specify game's name, ask for the name of the game.
        If the user greet you in any languages, greet back and introduce your self as 'GameFi Assistant'.
        Returns results in markdown format
        """
        messages = [{"role": "system", "content":system_message }] + history + [{"role": "user", "content": question}]

        stream = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=messages,
            # temperature=0.2,
            stream=True,
        )
        
        answer = ""
        
        for chunk in stream:
            token = chunk.choices[0].delta.content
            if token is not None:
                answer += token
                print(token)
                yield token
                
        user = {
            "role": "user",
            "content": question, 
            "rewrite_question": rewrite_question
        }
        
        assistant = {
            "role": "assistant",
            "content": answer,
            "context": context 
        }
        
        history = conversation['history']
        history.append(user)
        history.append(assistant)
        
        n_conversation = {
            'conversation_id': conversation['conversation_id'],
            'history': history
        }
        self.conversation_service.add_conversation(n_conversation)