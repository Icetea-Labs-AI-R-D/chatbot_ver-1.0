from dotenv import load_dotenv
from fastapi import Depends
from openai import OpenAI
import os
import json
from langsmith.wrappers import wrap_openai
from langsmith import traceable
from crud.conversation import add_conversation
from asgiref.sync import async_to_sync

load_dotenv()

class OpenAIService:
    openai_client: OpenAI
    def __init__(self) -> None:
        self.openai_client = wrap_openai(OpenAI(api_key=os.environ.get("OPENAI_API_KEY")))
        
    @traceable
    def rewrite_and_extract_keyword(self, message: str, conversation: list = [], global_topic: dict = None):
        if global_topic is None:
            global_topic = {'api': '', 'source': '', 'topic': '', 'type': ''}
        global_topic = global_topic.get('topic', "")
        
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
            ## Chat History ##
            {conversation}
            ## Global user's topic ##
            {global_topic}
            ## Current user's message ### 
            {message}
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
    
    @traceable
    def generate_suggestion(self, context: str = "[]"):
        system_prompt = '''
        You are a helpful agent designed to provide suggestions based on the user's message and context.
        Your suggestions are question prompts that can help the user to get more information about the game on GameFi.org. 
        The provided context contains a json string, so you should parse it and give suggestions based on ONLY the keys of the json.
        Generate exactly 3 question prompts.
        Suggest questions are in short, concise form, with upto 64 characters.
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
    
    @async_to_sync
    async def add_conversation_to_db(self, conversation_id, message):
            await add_conversation(conversation_id, message)
    @traceable
    def ask_openai_with_rag(self, question: str, conversation: list = [], context: str = "[]", global_topic: dict = None):
        if global_topic is None:
            global_topic = {'api': '', 'source': '', 'topic': '', 'type': ''}
        history = conversation.get('history', [])[-4:]
        system_message = f"""
        ###Task###
            You are a friendly and informative chatbot, you can introduce yourself as 'GameFi Assistant'. 
            YOUR TASK is to accurately answer information about games and IDO projects available on the GameFi platform, helping users better understand those information. 
            Use the following pieces of information to response the user's message: 
            <Information>
                {context}
            <Information>
            The information in this <Information> section is assigned "Context", please remember it.
            The user's question is assigned "User question", please remember to get it.

        ###Instructions###
            Please rely on the information of "Context" to answer "User question".
            Let's carefully analyze "Context" and "User question" to provide the best answer.
            When combining "Context" and "User question" to give the answer, the following possibilities arise:
            1. In "Context" there is information to answer the "User Question":
            - In this case, you can directly answer the "User question" based on the information in "Context".
            - Respond in a clear, concise and structured manner with all the information the user needs.
            - Do not answer questions like "This information is based on the data provided in the context".
            - Please present your answer as clearly and easily as possible to read, paragraphs that can have line breaks should be given line breaks
            2. In "Context" there is no information to answer the "User Question" or the information in "Context" is not related to "User Question":
            - In this case, you should answer that there is no information, and you can ask the user to provide more information or ask for clarification.
            - You can also ask the user if they have any other questions or need help with anything else.
            - Please respond in a friendly manner.
            3. "User question" are just normal communication questions (eg hello, thank you,...) that do not require information about games and IDO projects available on the GameFi platform:
            - In this case, please respond as normal communication.
            - You can also ask the user if they have any other questions or need help with anything else.
            - Please respond in a friendly manner.

        ###Note###
            Respond in a concise and structured manner and include all the information the user needs.
            Please present your answer as clearly and legibly as possible.
        """
        
        user_message = f"""
        ## Chat History ##
        {history}
        ## Current user's question ### 
        {question}
        """
        
        messages = [{"role": "system", "content":system_message }] + [{"role": "user", "content": user_message}]


        stream = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=messages,
            stream=True,
        )
        
        answer = ""
        
        for chunk in stream:
            token = chunk.choices[0].delta.content
            if token is not None:
                answer += token
                yield token
                
        suggestion = self.generate_suggestion(context)
        suggestion = json.loads(suggestion)
        reply_markup = {
            "text": "Maybe you want to know ⬇️:",
            "follow_up": suggestion['suggestions'][:3]
        }
        yield f"<reply_markup>{json.dumps(reply_markup)}</reply_markup>"     
        
        message = {
            "role_user": "user",
            "content_user": question, 
            "role_assistant": "assistant",
            "content_assistant": answer, 
            "global_topic": global_topic
        }
        

        self.add_conversation_to_db(conversation['conversation_id'], message)

