from openai import OpenAI
import os
from time import sleep
from .chroma_service import ChromaService
from .mongo_service import MongoService
import json

class OpenAIService:
    openai_client: OpenAI
    chroma_service: ChromaService
    mongo_service: MongoService
    global_topic: dict
    def __init__(self) -> None:
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.chroma_service = ChromaService()
        self.mongo_service = MongoService()
        self.global_topic = {'api': 'overview_gamehub', 'source': '', 'topic': 'gamehub', 'type': 'topic'}

    def _rewrite_and_extract_keyword(self, message: str, conversation: list = []):
        previous_message = ""
        if len(conversation) > 2: previous_message = conversation[-2]['content']
        
        system_prompt = f'''
        ### Task ###
        You are a helpful agent designed to paraphrase the user message into a complete sentence and extract the keywords.
        User message is question about GamFi, IDO,...

        ### Description Task ### 
        DO STEP BY STEP:
        1. Rewrite the user's message into a complete sentence.
        - In this step, first read the user's message carefully, then rewrite it to truly meet the user's intent.
        - Make sure to rewrite the user's message into a complete sentence.
        - At the end of this step, there will get a sentence called "rewritten_message".
        2. Extract the keyword from the user's message.
        - In this step, extract the keyword from the "rewritten_message" in step 1.
        - Keywords should be a list of words that are important in the user's message. They can be nouns, verbs, adjectives, etc.
        - Make sure to extract the keyword that is relevant to the user's message.
        - At the end of this step, there will get a list called "keywords".
        3. Provide a response to the user's message.
        - In this step, provide a response to the user's message.
        - Give the response in JSON format contains 2 keys: "rewritten_message" and "keywords".

        ### Note ###
        - The output should be a JSON format.
        '''

        user_message = f"""
            Previous user's message:{previous_message}
            Current user's message: 
                - User: {message}
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
    
    def generate_suggestion(self, context: str = "[]"):
        system_prompt = '''
        You are a helpful agent designed to provide suggestions based on the user's message and context.
        Your suggestions are question prompts that can help the user to get more information about the game on GameFi.org. 
        The provided context contains a json string, so you should parse it and give suggestions based on ONLY the keys of the json.
        Generate exactly 4 question prompts.
        Return the suggestions in JSON format contains 1 keys: "suggestions"
        '''

        user_message = f"""
        #### Context ####
        {context}
        #################    
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
                
        suggestion = self.generate_suggestion(context)
        suggestion = json.loads(suggestion)
        reply_markup = {
            "text": "Maybe you want know ⬇️:",
            "follow_up": suggestion['suggestions']
        }
        yield f"<reply_markup>{json.dumps(reply_markup)}</reply_markup>"
                
        user = {
            "role": "user",
            "content": question, 
        }
        
        assistant = {
            "role": "assistant",
            "content": answer
        }
        
        self.mongo_service.add_conversation(conversation['conversation_id'], user)
        self.mongo_service.add_conversation(conversation['conversation_id'], assistant)