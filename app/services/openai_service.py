from fastapi import Depends
from openai import AsyncOpenAI
import os
import json
from langsmith import traceable
from database.session import MongoManager
from database.queue import AsyncQueue
import random
from utils.tools_async import get_upcoming_IDO, get_infor_overview_gamefi
import utils.tools_async as tools
from typing import List
import ast
import re
from dotenv import load_dotenv
load_dotenv('.env')

class SuggestQuestion:
    id: str
    questions: list
    is_related: bool

def select_3_question_from_list(questions: List[SuggestQuestion], asked_ids: list = [], global_topic: dict = {}, question_dict: dict = {}):
    questions = list(filter(lambda x: x['id'] not in asked_ids, questions))
    
    force_rag = False
    # print(len(questions), global_topic['topic'])
    # Get all questions from topic if less than 3
    if len(questions) < 3 and 'upcoming' not in global_topic['topic'] and 'ido' not in global_topic['topic']:
        # print("###Less than 3 questions")
        force_rag = True
        # Filter api question and remove questions of upcoming game
        list_api = [key for key in question_dict.keys() if global_topic['topic'] in key and 'upcoming' not in key]
        sub_dict = dict(filter(lambda x: x[0] in list_api, question_dict.items()))
        
        for key, value in sub_dict.items():
            questions.extend([
                {
                    'id': v['id'],
                    'questions': v['questions'],
                    'is_related': v['is_related'],
                    'keyword': k
                }
            for k, v in value.items() if k != 'id']) 
        
    questions = list(filter(lambda x: x['id'] not in asked_ids, questions))
    
    related_questions = list(filter(lambda x: x['is_related'], questions))
    irrelated_questions = list(filter(lambda x: not x['is_related'], questions))
    
    num_related = min(2, len(related_questions))
    num_irrelated = min(3 - num_related, len(irrelated_questions))
    num_related = 3 - num_irrelated
    
    random.shuffle(related_questions)
    random.shuffle(irrelated_questions)
    
    related_questions = list(map(lambda x: 
        {
            'id': x['id'],
            'question':random.choice(x['questions']),
            'is_related' : False if force_rag else  x['is_related'],
            'keyword':  x['keyword']
        }, related_questions[:num_related]))
    irrelated_questions = list(map(lambda x:
        {
            'id': x['id'],
            'question':random.choice(x['questions']),
            'is_related' : False if force_rag else  x['is_related'],
            'keyword': x['keyword']
        }, irrelated_questions[:num_irrelated])) 
    
    list_question = [*related_questions, *irrelated_questions]    
    
    return list_question

# Use when rag is False to update lead sentence in context (rag is False -> selected_suggestions is not empty)
def reformat_context_for_no_rag(context: str, global_topic: dict = {}, selected_suggestions: list = []):
    list_context = re.split(r'\n{2,}' ,context.strip())
    
    keyword = selected_suggestions[-1]['keyword']
    for index, context in enumerate(list_context):
        if keyword in context:
            # Change lead sentence
            context = context.split('\n')
            context[0] = f"Information of {global_topic['source']} about {keyword}:"
            list_context[index] = '\n'.join(context)
            break
    return '\n' + '\n\n'.join(list_context)

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
        User message is a question about GamFi, IDO,...

        ### Description Task ### 
        DO STEP BY STEP:
        1. Extract the keyword from the user's message.
        - In this step, extract the keyword from the user's message.
        - Keywords should be a list of words that are important in the user's message. They can be nouns, verbs, adjectives, etc.
        - Make sure to extract the keyword that is relevant to the user's message.
        - At the end of this step, there will be a list called "keywords".
        2. Provide a response to the user's message.
        - In this step, provide a response to the user's message.
        - Give the response in JSON format containing 1 key: "keywords".

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
        conversation = conversation[-8:]
        if len(conversation) == 0:
            conversation = [{}]
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
        User history: {[f"{c['content']}" for c in conversation if c.get('role', '') == 'user']}
        Assistant last response: {conversation[-1].get('role', '')}: {conversation[-1].get('content', '')}  
        If the content is the same, you will be penalized.
        """
        # {nl.join(f"- {c['role']}: {c['content']}" for c in conversation if c['role'] == 'user')}
        user_message_list_ido = f"""
        Based on the list of questions and topics from assistant last response, topics are list of name IDO projects, provide suggested questions, up to 3 questions.
        Question list: {question_list}
        Assistant last response: {conversation[-1].get('role', '')}: {conversation[-1].get('content', '')}
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
    async def check_change_topic(
        self,
        topic_names: list,
        user_message: str,
        openai_client: AsyncOpenAI = None,
    ):
        nl = "    \n"
        
        system_prompt = f"""
You are a helpful agent!
Given a list of topics:
[
{nl.join([f'- Topic {index}: "{topic.lower()}"' for index, topic in enumerate(list(topic_names))])}
] 
Your task is to check if any of the topics in the list of topics is mentioned in the user's message.

Response in a JSON format like this:

{{
"is_mentioned": "True"/"False", 
"topic_index": index in list of topics
}}

Note:
- If the topic is mentioned in the user's message, set "is_mentioned" to "True" and set "topic_index" to the index of the topic in the list of topics.
- Let check very carefully.
- You will be penalized if you make a wrong answer.
        """

        user_message = f"""{user_message.lower()}"""       
        messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
        ]

        response = await openai_client.chat.completions.create(
            model="gpt-4o",
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
        context: str = "Empty",
        global_topic: dict = None,
        openai_client: AsyncOpenAI = None,
        features_keywords: dict = {},
        new_conversation: int = 0,
        selected_suggestions: list = [],
        rag: bool = True,
    ):
        if global_topic is None:
            global_topic = {"api": "", "source": "", "topic": "", "type": ""}
            
        if not rag and selected_suggestions != []:
            context = reformat_context_for_no_rag(context, global_topic, selected_suggestions)    
            
        history = conversation.get("history", [])[-4:]
        system_message = f"""
        You are a friendly and informative chatbot, you can introduce yourself as 'GameFi Assistant'. 
        YOUR TASK is to accurately answer information about IDO projects or Game World on GameFi.org, helping users better understand those information. 
        Answer the question based ONLY on the following context:
        Context: "{context}"

        Let carefully analyze the context and the user's question to provide the best answer.
        Answer BRIEFLY, with COMPLETE information and to the POINT of the user's question.
        The response style must be clear, easy to read, paragraphs that can have line breaks should be given line breaks.
        Note:
            - If the user's question is just normal communication questions (eg hello, thank you,...) that do not require information about available IDO projects or Game World on GameFi.org, please respond as normal communication.
            - If you can't find the information to answer the question in the context, please answer that you don't have information about that. 
        Let's make sure to provide a friendly, engaging, and helpful experience for the user!
        """

        user_message = f"""{question}"""

        messages = [{"role": "system", "content": system_message}] + history + [
            {"role": "user", "content": user_message}
        ]
        
        if new_conversation == 1:
            yield "<notify>✅ **Starting new dialog due to timeout**</notify>"

        answer = ""
        
        if global_topic.get('topic') == 'gamefi.org':
            answer = await get_infor_overview_gamefi()
            yield answer + "<stop>"
        else:
            stream = await openai_client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                temperature=0.7,
                messages=messages,
                # stream=True,
            )

            answer = stream.choices[0].message.content
            
            image_url_pattern = r'(https?://[^\s]+(?:\.jpg|\.jpeg|\.png|\.gif))'

            re_answer = re.sub(image_url_pattern, lambda match: f'<image>{match.group(0)}</image>', answer)
            
            re_answer += "<stop>"
            
            yield re_answer
            # Logic follow-up

            if rag == True :
                system_prompt = """
                You are a helpful agent!
                """
                
                prompt = f"""
                    You are given an answer and a user question. Based on these, you need to select the most appropriate keyword from the given list to answer the user's question.
                    ### Answer:
                    {answer}
                    ### User Question:
                    {question}
                    ### Keyword List:
                    {[(id, x['source']) for id, x in enumerate(features_keywords['content'])]}
                    ### Topic:
                    {global_topic['source']}
                    ### Task:
                    !It is not required to choose a keyword if it is not relevant enough.
                    Based on the topic, answer, and user's question, without using the topic, select only one keyword from the given list that is most relevant to answer the user's question.
                    Only select the keyword that is most relevant to the question and answer. If none of the keywords are suitable, please select 'None of the above' and return {{"id": -1}}.
                    ### Expected Result JSON format:
                    {{'id': index in the content list}}
                """ 
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]

                response = await openai_client.chat.completions.create(
                    model="gpt-3.5-turbo-0125",
                    temperature=0,
                    response_format={"type": "json_object"},
                    messages=messages,
                )

                key = response.choices[0].message.content
                index = json.loads(key).get('id', -1)
                
                if int(index) >= 0 and int(index) < len(features_keywords['content']):
                    content = features_keywords['content'][index]
                    relevant_question = self.question_dict.get(content.get('api', ""), {}).get(content.get('source', ""), {})
                    if relevant_question != {}: 
                        suggest = {
                            'id': relevant_question['id'],
                            'questions': relevant_question['questions'][0],
                            'is_related': relevant_question['is_related'],
                            'keyword': content.get('source', '')
                        }
                        selected_suggestions.append(suggest)
        ## Drop keys with no data
        def process_list_question_from_context(context : str, question_dict_api:dict ):
            data = dict()
           
            for item in re.split(r'\n{2,}' ,context.strip()):
                if len(item.split('\n')) > 0:
                    data.update(ast.literal_eval(item.split('\n')[1])) 
            
            keys = list(question_dict_api.keys())
            list_question = []
            
            
            if 'status' in data.get('data', {}) and type(data['data']['status']) == dict and data['data']['status'].get('isNull', False) == True:
                data['data']['status'] = None
            # Filter keys with no data
            tmp_dict = {**question_dict_api}
            for key in keys:
                tmp_val = data['data'].get(key, "")
                
                if (tmp_val == "" or tmp_val == None or tmp_val == 0 or tmp_val == [] or tmp_val == {}) and question_dict_api[key]['is_related']:
                    tmp_dict.pop(key)

            for k, v in tmp_dict.items():
                list_question.append({
                    'id': v['id'],
                    'questions': v['questions'],
                    'is_related': v['is_related'],
                    'keyword': k
                })
            
            return list_question
            
        
        selected_suggestion_ids = list(map(lambda x: x['id'], selected_suggestions))
        list_question = []
        suggestions = []
        
        
        if global_topic.get("source", "") == "upcoming":
            # assign keyword
            list_question = list(map(lambda item:
                {
                    'id': item[1][1]['id'],
                    'questions': item[1][1]['questions'],
                    'is_related' : item[1][1]['is_related'],
                    'keyword': item[1][0]
                }, enumerate(self.question_dict["overview_list_ido_upcoming"].items())))
            
            res = await tools.get_upcoming_endpoint_response()
            games_info = res.get('data', [])
            random.shuffle(list_question)
            random.shuffle(games_info)
            
            selected_questions = []
            selected_keywords = []
            
            for i in range(2):
                for index, game in enumerate(games_info):
                    for ques in list_question:
                        
                        if ques['keyword'] in selected_keywords:
                            continue
                        
                        if ques['keyword'] in game and game[ques['keyword']] != "" and game[ques['keyword']] != None and game[ques['keyword']] != 0 and game[ques['keyword']] != [] and game[ques['keyword']] != {}:
                            tmp_queston = {
                                'id': ques['id'],
                                'question': random.choice(ques['questions']).replace('<game-name>', game['name']),
                                'is_related' : False,
                            }
                            selected_questions.append(tmp_queston)
                            selected_keywords.append(ques['keyword'])
                            break
                    if len(selected_questions) == 3:
                        break
                if len(selected_questions) == 3:
                        break
            list_question = selected_questions[:3]       
         
                    
            suggestions =  [item['question'] for index, item in enumerate(list_question)]
        
        elif global_topic.get('topic') == 'gamefi.org':
            list_question = self.question_dict["general"][1:4]
            suggestions = list_question
            list_question = list(map(lambda x:
                {
                    'id': 1000,
                    'question': x,
                    'is_related' : False,
                    'keyword': ""
                }, list_question))
        
        elif global_topic.get("source", "") == "":
            list_question = self.question_dict["general"][:3]
            suggestions = list_question
            list_question = list(map(lambda x:
                {
                    'id': 1000,
                    'question': x,
                    'is_related' : False,
                    'keyword': ""
                }, list_question))
        else:
            list_unique_api = list(
                set([c.get("api", "") for c in features_keywords.get("content", [])])
            )
            list_question = []
                    
            for api in list_unique_api:
                if api != "":
                    processed_list_question = process_list_question_from_context(context, self.question_dict[api])
                    list_question.extend(processed_list_question)

            is_content_empty = False
            if features_keywords.get("content", []) == []:
                is_content_empty = True
                topic = features_keywords.get("topic", {})
                if topic != {} and topic.get("api", "") != "":
                    processed_list_question = process_list_question_from_context(context, self.question_dict[topic["api"]])
                    list_question = processed_list_question

            list_question = select_3_question_from_list(list_question, asked_ids=selected_suggestion_ids, global_topic=global_topic, question_dict=self.question_dict)
          
            pattern = r'[ \-_]+' 
            
            game_name = ' '.join([word.capitalize() for word in re.split(pattern, global_topic['source'])])
            list_question = list(map(lambda x:
                    {
                        'id': x['id'],
                        'question': x['question'].replace('<game-name>', game_name),
                        'is_related' :  False if is_content_empty else x['is_related'],
                        'keyword': x['keyword']
                    }, list_question))
            
            suggestions = [item['question'] for item in list_question]
        
        # print(suggestions)
        reply_markup = {
            "text": "Maybe you want to know ⬇️:",
            "follow_up":suggestions,
        }
        # If suggestions is not empty, return suggestions
        if len(suggestions) != 0 and global_topic.get('topic', '') != 'end_phrase':
            # print('yield reply_markup')
            yield f"<reply_markup>{json.dumps(reply_markup)}</reply_markup>"

        # yield "<stop>"
        # print(suggestions)
        
        message = {
            "content_user": question,
            "content_assistant": answer,
            "topic": global_topic,
            "suggestion": list_question,
            "context": context,
            "features_keywords": features_keywords,
            "selected_suggestions": selected_suggestions,
        }

        await self.async_queue.put(openai_client)
        await self.db.add_conversation(conversation["conversation_id"], message)

    async def list_upcoming_ido(self, conversation_id):
        res = await get_upcoming_IDO("")
        nl = '\n'
        out = f"""Here are the upcoming IDO projects on GameFi:\n{nl.join([f"{index+1}. {item}" for index, item in enumerate(res['list_project'])])}\nThese projects are part of the upcoming IDOs (Initial DEX Offerings) on the GameFi platform."""
        # print(out)
        for line in out.split("\n"):
            yield line + '\n'

        yield "<stop>"
        
        list_game_name = [item for item in res['list_project']]
        random.shuffle(list_game_name)
        
        # item = {index: (key, value)}
        # assign keyword
        list_question = list(map(lambda item:
            {
                'id': item[1][1]['id'],
                'questions': item[1][1]['questions'],
                'is_related' : item[1][1]['is_related'],
                'keyword': item[1][0]
            }, enumerate(self.question_dict["overview_list_ido_upcoming"].items())))
        
        list_question = select_3_question_from_list(list_question)
        
        # Map game names
        list_question = list(map(lambda item:
            {
                'id': item[1]['id'],
                'question': item[1]['question'].replace('<game-name>', list_game_name[item[0] if item[0] < len(list_game_name) else random.randint(0, len(list_game_name)-1)]),
                'is_related' : item[1]['is_related']
            }, enumerate(list_question)))
        
        suggestions =  [item['question'] for index, item in enumerate(list_question)]
        
        if len(suggestions) != 0:
            reply_markup = {
                "text": "Maybe you want to know ⬇️:",
                "follow_up":suggestions,
            }
            # print('yield lskdjflsfd')
            yield f"<reply_markup>{json.dumps(reply_markup)}</reply_markup>"
            
        message = {
            "content_user": "list upcoming ido",
            "content_assistant": out,
            "topic": {'api': 'overview_list_ido_upcoming', 'source': 'upcoming', 'topic': 'list_ido_upcoming', 'type': 'topic'},
            "suggestion": list_question,
            "context": "",
            "features_keywords": {},
            "selected_suggestions": [],
        }
        await self.db.add_conversation(conversation_id, message)
        
    async def games(self, conversation_id):
        out = """
        Here is the formatted list of available games on GameFi:

        1. Mobox
        2. The Sandbox
        3. BinaryX
        4. Axie Infinity
        5. X World Games
        6. Thetan Arena
        7. Alien Worlds
        8. League of Kingdoms
        9. BurgerCities
        10. Kryptomon
        ...

        For more details and the full list of games, visit the official [GameFi website](https://gamefi.org).
        """
        yield out
        yield "<stop>"
        
        message = {
            "content_user": "list games",
            "content_assistant": out,
            "topic": {},
            "suggestion": [],
            "context": "",
            "features_keywords": {},
            "selected_suggestions": [],
        }
        await self.db.add_conversation(conversation_id, message)