from fastapi import Depends
from openai import AsyncOpenAI
import os
import json
from langsmith import traceable
from database.session import MongoManager
from database.queue import AsyncQueue
from utils.static_param import new_conversation_generator
import random


class OpenAIService:
    db: MongoManager
    async_queue: AsyncQueue
    question_dict: dict

    def __init__(self) -> None:
        self.db = MongoManager()
        self.async_queue = AsyncQueue()
        path_to_json = os.path.join(
            os.path.dirname(__file__), "../../data/json/questions.json"
        )
        with open(path_to_json) as f:
            self.question_dict = json.load(f)

    @traceable
    async def rewrite_and_extract_keyword(
        self,
        message: str,
        conversation: list = [],
        global_topic: dict = None,
        openai_client: AsyncOpenAI = None,
    ):
        if global_topic is None:
            global_topic = {"api": "", "source": "", "topic": "", "type": ""}
        global_topic = global_topic.get("topic", "")

        system_prompt = """
        ### Task ###
        You are a helpful agent designed to paraphrase the user message into a complete sentence and extract the keywords.
        User message is question about GamFi, IDO,...

        ### Description Task ### 
        DO STEP BY STEP:
        1. Extract the keyword from the user's message.
        - In this step, extract the keyword from the user's message.
        - Keywords should be a list of words that are important in the user's message. They can be nouns, verbs, adjectives, etc.
        - Make sure to extract the keyword that is relevant to the user's message.
        - At the end of this step, there will get a list called "keywords".
        2. Provide a response to the user's message.
        - In this step, provide a response to the user's message.
        - Give the response in JSON format contains 1 keys: "keywords".

        ### Note ###
        - The output should be a JSON format.
        """

        user_message = f"""
            Current user's message: {message}
        """
        messages = [{"role": "system", "content": system_prompt}] + [
            {"role": "user", "content": user_message}
        ]

        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            temperature=0,
            response_format={"type": "json_object"},
            messages=messages,
        )
        return str(response.choices[0].message.content)

    @traceable
    async def generate_suggestion(
        self,
        context: str = "[]",
        openai_client: AsyncOpenAI = None,
        conversation: list = [],
        question_list: str = [],
        global_topic: dict = {},
    ):
        conversation = conversation[-10:]
        system_prompt = f"""
        You are a helpful agent designed to provide suggestions based on the user's message and context.
        Your role is to pick randomly up to 3 questions from provided question list that are most relevant to the user's message.
        Return the suggestions in JSON format contains 1 keys: "suggestions"
        {{
            "suggestions": ["Question 1", "Question 2", "Question 3"]    
        }}
        
        Note:
           - Question X should be the question from the question list that is provided in the user input. 
           - If there are less than 3 questions in the question list, return all questions in the list.
        """
        nl = "\n"

        # Shuffle question list
        random.shuffle(question_list)

        user_message = f"""
        Based on the list of questions and topics below, provide suggested questions, up to 3 questions.
        Question list: {question_list}
        Of course,naturally add the topic below to each question, while keeping the structure of each question in the list the same, if topic is empty, don't add it.
        Topic: {global_topic['source']}
        Carefully check whether the suggested question has content that matches the user's message history or the Assistant's last response. If the content is the same, the suggestion will not be added.
        User history: {[f"{c['content']}" for c in conversation if c['role'] == 'user']}
        Assistant last response: {conversation[-1]['role']}: {conversation[-1]['content']}  
        If the content is the same, you will be penalized.
        """
        # {nl.join(f"- {c['role']}: {c['content']}" for c in conversation if c['role'] == 'user')}
        user_message_list_ido = f"""
        Based on the list of questions and topics from assistant last response, topics are list of name IDO projects, provide suggested questions, up to 3 questions.
        Question list: {question_list}
        Assistant last response: {conversation[-1]['role']}: {conversation[-1]['content']}
        Can take many random name IDO project from Assistant last response.
        Check the user's message history to avoid repeating the same question.
        User history: {[f"{c['content']}" for c in conversation if c['role'] == 'user']}
        """
        if global_topic["api"] == "overview_list_ido_upcoming":
            messages = [{"role": "system", "content": system_prompt}] + [
                {"role": "user", "content": user_message_list_ido}
            ]
        else:
            messages = [{"role": "system", "content": system_prompt}] + [
                {"role": "user", "content": user_message}
            ]

        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            temperature=0,
            response_format={"type": "json_object"},
            messages=messages,
        )

        return str(response.choices[0].message.content)

    @traceable
    async def ask_openai_with_rag(
        self,
        question: str,
        conversation: list = [],
        context: str = "[]",
        global_topic: dict = None,
        openai_client: AsyncOpenAI = None,
        features_keywords: dict = {},
        new_conversation: int = 0,
    ):
        if global_topic is None:
            global_topic = {"api": "", "source": "", "topic": "", "type": ""}
        history = conversation.get("history", [])[-4:]
        system_message = """
        You are a friendly and informative chatbot, you can introduce yourself as 'GameFi Assistant'. 
        YOUR TASK is to accurately answer information about games and IDO projects available on the GameFi platform, helping users better understand those information. 
        Based on the context below, answer the user's question.
        Let carefully analyze the context and the user's question to provide the best answer.
        
        Answer BRIEFLY, with COMPLETE information and to the POINT of the user's question.
        The response style must be clear, easy to read, paragraphs that can have line breaks should be given line breaks.
        Note:
            - If you can't find the information to answer the question, please answer that you couldn't find the information.
            - If the user's question is just normal communication questions (eg hello, thank you,...) that do not require information about games and IDO projects available on the GameFi platform, please respond as normal communication.
        """

        user_message = f"""
        Chat History: {history}
        Answer the question based only on the following context:
        Context: {context} 
        User: {question}
        """

        messages = [{"role": "system", "content": system_message}] + [
            {"role": "user", "content": user_message}
        ]
        
        if new_conversation == 1:
            async for chunk in new_conversation_generator(1):
                yield f"<reply_markup>{chunk}</reply_markup>"

        stream = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=messages,
            stream=True,
        )

        answer = ""

        async for chunk in stream:
            token = chunk.choices[0].delta.content
            if token is not None:
                answer += token
                yield token

        # Logic follow-up
        list_unique_api = list(
            set([c.get("api", "") for c in features_keywords.get("content", [])])
        )
        list_question = []
        for api in list_unique_api:
            if api != "":
                list_question.extend(self.question_dict[api])

        if features_keywords.get("content", []) == []:
            topic = features_keywords.get("topic", {})
            if topic != {} and topic.get("api", "") != "":
                list_question = self.question_dict.get(topic["api"], [])

        if global_topic["source"] == "":
            list_question = self.question_dict["general"]

        if global_topic["source"] == "upcoming":
            list_question = self.question_dict["overview_list_ido_upcoming"]

        conversation["history"].append({"role": "user", "content": question})
        conversation["history"].append({"role": "assistant", "content": answer})

        suggestion = await self.generate_suggestion(
            context=context,
            conversation=conversation["history"],
            question_list=list_question,
            global_topic=global_topic,
            openai_client=openai_client,
        )
        suggestion = json.loads(suggestion)
        reply_markup = {
            "text": "Maybe you want to know ⬇️:",
            "follow_up": suggestion["suggestions"][:3],
        }
        yield f"<reply_markup>{json.dumps(reply_markup)}</reply_markup>"

        message = {
            "content_user": question,
            "content_assistant": answer,
            "topic": global_topic,
            "suggestion": suggestion["suggestions"][:3],
            "context": context,
            "features_keywords": features_keywords,
        }

        await self.async_queue.put(openai_client)
        await self.db.add_conversation(conversation["conversation_id"], message)
