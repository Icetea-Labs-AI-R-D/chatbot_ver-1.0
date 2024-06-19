import requests
import json
import asyncio
import httpx
from datetime import datetime, timezone
from async_lru import alru_cache
# from langchain.docstore.document import Document
# from langchain_community.vectorstores import Chroma
# from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import chromadb

load_dotenv('.env')

list_ido_game = []
# OpenAI embeddings
embedding_function = OpenAIEmbeddingFunction(api_key=os.getenv('OPENAI_API_KEY3'))
chroma_client = chromadb.HttpClient(host='chroma')  
# chroma_client = chromadb.HttpClient()  
async def get_upcoming_IDO_with_slug():
    url = "https://ido.gamefi.org/api/v3/pools/upcoming"
    headers = {
        "Accept": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response_json = response.json()
    
    list_project_name = []
    data = response_json['data']
    for item in data:
        list_project_name.append(
            {
               'name': item['name'],
               'slug': item['slug']
            }
        )
    
    overview = {
        "number_of_upcoming_IDO": len(list_project_name),
        "list_project": list_project_name
    }
    
    return overview


async def update_topic_vector_db(vector_db):
    print(f"Total items in vector {vector_db.name} before update: {vector_db.count()}")
    # Remove old ido_upcoming topic from vector_db
    list_old_ids = list(filter(lambda x: x.startswith('ido_upcoming') ,vector_db.get()['ids']))
    # print(list_old_ids)
    if not list_old_ids : list_old_ids = ['']
    vector_db.delete(ids=list_old_ids)
    
    # Get new ido_upcoming topic
    new_data = await get_upcoming_IDO_with_slug()
    
    # Update new ido_upcoming topic to vector_db
    new_topic_ido_upcoming = new_data['list_project']
    new_topic = []
    for doc in new_topic_ido_upcoming:
        # document = Document(page_content=doc['name'], metadata={'api': 'overview_ido_upcoming', 'source': doc['slug'], 'type': 'topic', 'topic': 'ido_upcoming'})
        item = {
            'page_content': doc['name'],
            'metadata': {'api': 'overview_ido_upcoming', 'source': doc['slug'], 'type': 'topic', 'topic': 'ido_upcoming'}
        }
        new_topic.append(item)
        item = {
            'page_content': doc['slug'],
            'metadata': {'api': 'overview_ido_upcoming', 'source': doc['slug'], 'type': 'topic', 'topic': 'ido_upcoming'}
        }
        new_topic.append(item)
    # print(new_topic)
    vector_db.add(
        documents=[item['page_content'] for item in new_topic], 
        ids=[f'ido_upcoming_{i+1}' for i in range(len(new_topic))],
        metadatas=[item['metadata'] for item in new_topic]
    )
    
    print(f"Added {len(new_topic)} items to vector {vector_db.name}")
    print(f"Total items in vector {vector_db.name} after update: {vector_db.count()}")

@alru_cache(maxsize=32, ttl=60**3)
async def get_infor_overview_gamehub(name, keywords=[]):
    """Get token price, market cap, and other tokenomics information from GameFi API."""
    
    url = f'''https://v3.gamefi.org/api/v1/games/{name}?include_tokenomics=true&include_studios=true&include_downloads=true&include_categories=true&include_advisors=true&include_backers=true&include_networks=true&include_origins=true&include_videos=true'''
    headers = {
        'Accept': 'application/json'
    }
    description = {
        "status": "The state of the game whether is is publishted or not",
        "avg_star_rating": "The average star rating of the project on gamefi.org",
        "dislikes": "Number of dislikes",
        "likes": "Number of likes",
        "ratings": "Number of ratings",
        "reviews": "Number of reviews",
        "score": "Rating score",
        "market_cap": "The total market value of a cryptocurrency's circulating supply. It is analogous to the free-float capitalization in the stock market.The total market value of the token or cryptocurrency used within the game. This information provides an overview of the market size for that token or cryptocurrency, often used to assess the stability and growth potential of the project.",
        "market_cap_fully_diluted": "The total market value of all tokens or cryptocurrencies that could exist if all those tokens or cryptocurrencies were issued and circulating in the market. This information provides an overview of the maximum value that the project could achieve if all tokens or cryptocurrencies were issued and sold.",
        "token_symbol": "The symbol of the token of the game",
        "highest_price": "ATH price / The highest price that a token or cryptocurrency has reached since it was first listed on the market. ATH stands for \"All-Time High,\" and this information provides an overview of the highest price the token has achieved in the past. It can be used to assess the performance and growth potential of the token in the future.",
        "current_price": "Current token's price",
        "public_price": "Token's IDO price",
        "init_token_circulation": "Circulating Supply / The amount of coins that are circulating in the market and are in public hands. It is analogous to the flowing shares in the stock market.",
        "price_change_24_h": "Percentages in price change compare to the previous 24 hours period",
        "price_change_7_d": "Percentages in price change compare to the previous 7 days period",
        "price_change_30_d": "Percentages in price change  compare to the previous 30 days period",
        "price_change_90_d": "Percentages in price change  compare to the previous 90 days period",
        "volume_24_h": "The trading volume of the token or cryptocurrency used within the game over the past 24 hours. This information provides insight into the level of activity and interaction of the player community with that token or cryptocurrency on trading platforms, reflecting market activity and liquidity.",
        "volume_change_24_h": "The measure of how many percentages in token's volume change compare to the previous 24 hours period.",
        "total_supply": "The total number of coins/tokens in circulation on the market, excluding the amount that is locked, minus the amount that has been burned.",
        "max_supply": "The total maximum number of tokens coins/tokens that will ever exist, including both mined and future available tokens. This information provides an overview of the limitations on the token's supply and helps readers understand the project's economic structure.",
        "published_at": "The date when the game was published or released",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response = response.json()
    gameId = response['data']['item'].get('id', "")
    nameGame = response['data']['item'].get('name', "")
    status = response['data']['item'].get('status', "")
    published_at = response['data']['item'].get('published_at', "")
    white_paper = response['data']['item'].get('white_paper', "")
    banners = response['data']['item'].get('banners', "")
    introduction = response['data']['item'].get('introduction', "")
    play_to_earn_model = response['data']['item'].get('play_to_earn_model', "")
    links = response['data']['item'].get('links', "")
    ratingScore = response['data']['metadata'].get('counts', {}).get(gameId, "")
    tokenomicsCompact = response['data']['item'].get('tokenomics_compact', "")
    studios = response['data']['item'].get('studios', "")
    studios = [studio['name'] for studio in studios]
    
    roadmap_text = response['data']['item'].get('roadmap_text', None)
    if roadmap_text:
        roadmap_text = json.loads(roadmap_text)
        roadmap = roadmap_text.get('blocks', [])
        roadmap_text = ""
        for block in roadmap:
            data = block.get('data', {})
            if data.get('text','') != '':
                roadmap_text += data.get('text','') + "\n"
            if data.get('items',[]) != []:
                roadmap_text += "\n".join(data.get('items',[])) + "\n"
    play_mode = response['data']['item'].get('play_mode', None)
    if play_mode:
        play_mode = json.loads(play_mode)
        play_mode = play_mode.get('blocks', [])
        play_mode_text = ""
        for block in play_mode:
            data = block.get('data', {})
            if data.get('text','') != '':
                play_mode_text += data.get('text','') + "\n"
            if data.get('items',[]) != []:
                play_mode_text += "\n".join(data.get('items',[])) + "\n"
        play_mode = play_mode_text
    
    introduction = response['data']['item'].get('introduction', None)    
    if introduction:
        if type(introduction) == str:
            introduction = json.loads(introduction)
        introduction = introduction.get('blocks', [])
        introduction_text = ""
        for block in introduction:
            data = block.get('data', {})
            if data.get('text','') != '':
                introduction_text += data.get('text','') + "\n"
            if data.get('items',[]) != []:
                introduction_text += "\n".join(data.get('items',[])) + "\n"
        introduction = introduction_text

    play_to_earn_model = response['data']['item'].get('play_to_earn_model', None)    
    if play_to_earn_model:
        if type(play_to_earn_model) == str:
            play_to_earn_model = json.loads(play_to_earn_model)
        play_to_earn_model = play_to_earn_model.get('blocks', [])
        play_to_earn_model_text = ""
        for block in play_to_earn_model:
            data = block.get('data', {})
            if data.get('text','') != '':
                play_to_earn_model_text += data.get('text','') + "\n"
            if data.get('items',[]) != []:
                play_to_earn_model_text += "\n".join(data.get('items',[])) + "\n"
        play_to_earn_model = play_to_earn_model_text
    
    overview = {
        "data": {
            "name": nameGame,
            "status": status,
            "published_at": published_at,
            "white-paper": white_paper,
            "banners": banners,
            "introduction": introduction,
            "roadmap-text": roadmap_text,
            "play-mode": play_mode,
            "play-to-earn-model": play_to_earn_model,
            "social-media": links,
            "rating-score": ratingScore,
            # "tokenomics-compact": tokenomicsCompact,
            "studios": studios,
            **tokenomicsCompact[0]
        },
        "description": description
    }
    if len(keywords) == 0:
        overview = {
            "data": {
                "name": nameGame,
                "status": status,
                # "published_at": published_at, 
                "introduction": introduction,
                "social-media": links,
                "tokenomics-compact": tokenomicsCompact,
            }
        }
    # else:
    #     list_key_to_pop = [i for i in list(overview['data'].keys()) if i not in keywords]
    #     for key in list_key_to_pop:
    #         overview['data'].pop(key)
    return overview

@alru_cache(maxsize=32, ttl=60**3)
async def get_on_chain_performance_gamehub(name, keywords=[]):
    """Get game on-chain performance from GameFi API."""
   
    description = {
        "uaw_7d_changed": "The change in the number of individual electronic wallets participating in transactions over the past 7 days.",
        "nft_transaction_7d_changed": "The change in the number of NFT transactions in the past 7 days.",
        "volume_rank": "Trading volume ranking",
        "market_cap_rank": "Market capitalization ranking",
        "uaw_rank": "Ranking total number of individual electronic wallets performing transactions.",
        "nft_transaction_rank": "Ranking based on total number of NFT transactions",
        "onchain_rank": "On-chain ranking level of the game",
        "market_rank": "Top games with the highest scores on the page"
    }
    url = f'''https://v3.gamefi.org/api/v1/games/{name}/on-chain-performance'''
    headers = {
        'Accept': 'application/json'
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response = response.json()
    data = response.get('data', {})
    data.pop('game_id', None)
    if data == {}:
        description = {}
    res = {
        "data": data,
        "description": description
    }
    return res

@alru_cache(maxsize=32, ttl=60**3)
async def get_community_performance_gamehub(name, keywords=[]):
    """Get community performance of a game from GameFi API."""
    
    description = {
        "market_rank": "Top games with the highest scores on the page",
        "telegram_group_users": "The number of users participating in Telegram.",
        "twitter_followers": "Number of followers on Twitter",
        "discord_users": "The number of users on Discord is counted on the Gamefi.org page.",
        "community_rank": "Community rank on Gamefi.org",
        "twitter_rank": "Rank on Gamefi.org of project's twitter page",
        "telegram_group_rank": "Rank on Gamefi.org of project's group on telegram",
        "discord_rank": "Rank on Gamefi.org of project's discord group"
    }
    url = f'''https://v3.gamefi.org/api/v1/games/{name}/community-performance'''
    headers = {
        'Accept': 'application/json'
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response = response.json()
    try:
        data = response['data']
        data.pop('game_id', None)
    except:
        data = {}
        description = {}
    res = {
        "data": data,
        "description": description
    }
    return res
@alru_cache(maxsize=32, ttl=60**3)
async def get_daily_index_gamehub(name, keywords=[]):
    """Get daily ranking, social score, uaw, transaction and holder information in the last 24 hours of a game from GameFi API."""
   
    description = {
        "gamefi_ranking": "General ranking of Games on the Gamefi.org page",
        "social_signal_24h": "Social signals index in the last 24 hours.",
        "social_score_24h": "Social score in the past 24 hours.",
        "uaw_24h": "Number of unique wallets participating in transactions in 24 hours.",
        "transactions_24h": "The number of transactions carried out in the last 24 hours.",
        "holders_24h": "The number of users holding tokens or NFTs in the last 24 hours."
    }
    url = f'''https://v3.gamefi.org/api/v1/games/{name}/overview'''
    headers = {
        'Accept': 'application/json'
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response = response.json()
    try:
        data = response['data']
    except:
        data = {}
        description = {}
    return {
        "data": data,
        "description": description
    }
    
@alru_cache(maxsize=32, ttl=60**3)
async def get_social_score_gamehub(name, keywords=[]):
    """Get social score of a game from GameFi API."""
    
    description = {
        "time": "Time that records social score",
        "time_frame": "Time frame",
        "social_score": "Overall project social's score on GameFi.org",
        "telegram_score": "Telegram score",
        "telegram_group_score": "Score on Gamefi.org of project's group on telegram",
        "telegram_channel_score": "Score on Gamefi.org of project's channel on telegram",
        "social_rank": "Overall project social's rank on GameFi.org",
        "telegram_channel_rank": "Rank on Gamefi.org of project's channel on telegram"
    }
    url = f'''https://v3.gamefi.org/api/v1/games/{name}/social-scores'''
    headers = {
        'Accept': 'application/json'
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response = response.json()
    try:
        item = response['data']['item']
        item.pop('game_id', None)
    except:
        item = {}
        description = {}
    res = {
        "data": item,
        "description": description
    }
    return res

@alru_cache(maxsize=32, ttl=60**3)
async def get_top_backers_gamehub(name, keywords=[]):
    """Get all backers of a game from GameFi API."""
    
    url = f'''https://v3.gamefi.org/api/v1/games/{name}/top-backers'''
    headers = {
        'Accept': 'application/json'
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response = response.json()
    listBacker = []
    try:
        items = response['data']['items']
        for index, item in enumerate(items):
            name = response['data']['items'][index]['name']
            linkWebsite = response['data']['items'][index]['links']['website']
            listBacker.append(
                {
                    "name": name,
                    "link-website": linkWebsite 
                }
            )
    except:
        listBacker = []
    backers = {
        "data": {
            "backer" : listBacker
        } 
    }
    return backers

def to_date(time):
    return str(datetime.fromtimestamp(time, timezone.utc))

@alru_cache(maxsize=32, ttl=60**3)
async def get_overview_ido(name, keywords=[]):

    description = {
        "slug": "Abbreviation for the project name.",
        "name": "Name of project.",
        "description": "Providing an overview of the project",
        "status": "Status of the IDO.",
        "claim_policy": "Vesting / includes the vesting period, release rate, and any other provisions regarding the trading freedom of tokens after the IDO.",
        "total_token": "Total number of tokens available for the IDO.",
        "ath": "The maximum return on investment that the project's token has achieved since its all-time high.",
        "whitelist": "The timeframe during which the whitelist is open to receive registrations from individuals who want to participate in the project's IDO.",
        "refund_policy": "The policy regarding refunding funds in case the IDO is unsuccessful or if any issues arise. This information may include the conditions and regulations for requesting a refund, the timeframe, and the process for refunding.",
        "buying_phases": "The time or period during which users can purchase tokens or participate in the project's IDO.",
        "token": {
            "type": "The specific category or standard this token adheres to, defining its functionality and interaction within its respective blockchain ecosystem.",
            "symbol": "The unique identifier or abbreviation for this token, used for trading and referencing in the cryptocurrency markets.",
            "price": "The current market value of the token, often quoted in United States Dollars (USD), which can fluctuate based on supply and demand dynamics.",
            "decimals": "The maximum number of decimal places to which this token can be subdivided, indicating the smallest possible transaction unit for this token."
        },
        "currency": {
            "type": "The unique symbol identifying the currency",
            "decimals": "Defines the smallest unit of the currency that can be handled in transactions."
        },
        "social_networks": "Provide information about the links to the project's social media pages or social media platforms of IDO project.",
        "roadmap": "The project's roadmap, which outlines the key milestones and objectives that the project aims to achieve in the future.",
        "revenue_streams": "Provide information about the sources of income that the project is expected to generate during its operation.",
        "token_utilities": "Provide information about the applications and features that the project's token will provide.",
        "highlights": "Provide information about the unique and standout aspects of the project. This information may include significant achievements, advanced technologies utilized, competitive advantages, market opportunities, or any other strengths that the project aims to highlight to attract the attention of the community and potential investors during the IDO process",
        "launchpad": "The platform or service that is hosting the IDO for the project.",
        "total_raise": "The total amount of funds the project aims to raise through the Initial DEX Offering (IDO) process and other funding rounds. This information provides an overview of the level of attractiveness and interest from the community and potential investors towards the project."
    }

    url = f'''https://ido.gamefi.org/api/v3/pool/{name}'''
    headers = {
        'Accept': 'application/json'
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response = response.json()
    data = response.get('data', {})
    # data['about'] = data.drop('description')
    if data == None:
        return {
            "description": {},
            "data": {}
        }
    # Remove key in data
    remove_keys = ['id', 'chain_id', 'excerpt', 'address', 'logo', 'banner', 'contract_address', 'address_receiver', 'airdrop_chain_id', 'claim_schedule']
    for key in  remove_keys:
        if key in data:
            data.pop(key)
    # Remove key in token
    token = data['token']
    for key in remove_keys:
        if key in token:
            token.pop(key)
    data['token'] = token

    # Remove key in currency
    currency = data['currency']
    for key in remove_keys:
        if key in currency:
            currency.pop(key)
    data['currency'] = currency

    # Change the format of the date
    date_keys = ['from', 'to', 'claimed_at']
    for key in date_keys:
        if data['whitelist'].get(key) is not None:
            data['whitelist'][key] = to_date(data['whitelist'][key])
    for key in date_keys:
        if data['refund_policy'].get(key) is not None:
            data['refund_policy'][key] = to_date(data['refund_policy'][key])
    for item in data['buying_phases']:
        item.pop('id')
        for key in date_keys:
            if item.get(key) is not None:
                item[key] = to_date(item[key])
    
    # Cup the story, roadmap, revenue_streams, token_utilities
    story = ""
    main_story = ""
    for item in data['story']['blocks']:
        if item['type'] == 'header':
            header = item['data'].get('text')
            if "Roadmap" in header:
                main_story = story
                story = ""
            if "Revenue Streams" in header:
                if "Roadmap" in story:
                    data['roadmap'] = story
                else:
                    data['token_utilities'] = story
                story = ""
            if "Token Utilities" in header:
                if "Roadmap" in story:
                    data['roadmap'] = story
                elif "Revenue Streams" in story:
                    data['revenue_streams'] = story
                else:
                    main_story = story
                story = ""
        if item['data'].get('text') is not None:
            story += item['data'].get('text') + "\n"
        if item['data'].get('items') is not None:
            for txt in item['data'].get('items'):
                story += txt + "\n"
    data.pop('story')
    data['highlights'] = main_story
    if "Token Utilities" in story:
        data['token_utilities'] = story
    else:
        data['revenue_streams'] = story
    total_raise = data['total_token'] * data['token']['price']
    data['total_raise'] = total_raise
    
    
    
    overview = {
        "description": description,
        "data": data
    }
    
    
    if len(keywords) == 0:
        overview = {
            "description": {
                "name" : description['name'],
                "description": description['description'],
                "status": description['status'],
                "token": description['token'],
                "social_networks": description['social_networks'],
            },
            "data": {
                "name" : data['name'],
                "description": data['description'],
                "status": data['status'],
                "token": data['token'],
                "social_networks": data['social_networks'],
            }
        }
    
    return overview

@alru_cache(maxsize=32, ttl=60**3)
async def get_tokenomics_gamehub(name, keywords=[]):
    listID = {'mobox': 'cda1dd30-0128-4ffe-bb65-29001e1ad0e9', 'the-sandbox': '08c1027f-4984-487a-a968-3c710ef2bd00', 'binaryx': '9e2def2a-f701-4721-a2c7-925b83018adf', 'axie-infinity': 'f96d0db8-d551-40c3-905c-e6e002c920e3', 'x-world-games': 'ffb52c78-016e-44f1-bfea-b57286d91898', 'thetan-arena': '149b050a-f391-4397-8dc0-163ea2e14138', 'alien-worlds': '0c49e040-be09-40ee-a178-e77bf404796e', 'league-of-kingdoms': '5293cb42-c26e-4a32-b80e-f595adc07083', 'burgercities': 'b91204b9-4197-4e4a-b5c7-56343ef49141', 'kryptomon': '0b54a231-070a-4474-ad6e-a17afba9a6c6', 'wanaka-farm': '466a5862-7e68-467b-85ef-cb677f5e96c5', 'sidus-heroes': '04054d55-b1ec-4234-9f10-c789b3b56065', 'ninneko': 'd2f84664-d28d-4729-8a0a-0ed33c39c521', 'cryptoblades': 'ad82204a-23d5-4ffe-a1ae-f8fb1f71b5f7', 'ultimate-champions': 'a1ee2386-33de-47cc-a3fe-11d0342de2e9', 'monsterra': 'b0b1271c-7b48-4bdc-a555-6ce95fc8bdfe', 'polychain-monsters': '47e03d0d-c353-47b0-b99c-a2a82dd875ae', 'iguverse': 'a47d016f-76e8-4f9c-819d-7c81daad7e91', 'heroes-empires': '79075231-aa7d-4b52-97d5-4390521f108b', 'illuvium': 'd3bf9ecf-58f1-488d-a3dc-8bead33eb930', 'xana': '3a0e8a04-255b-435b-856c-0723c01f08db', 'aqua-farm': '9a6373c8-9c46-40b5-9d23-c4fcbe873b20', 'mines-of-dalarnia': '60424918-41f0-4334-9ce3-2671f1febe88', 'magiccraft': 'a3110df8-f298-483c-aa0b-ce4fcae44841', 'derace': '31dcd5f2-5293-4db4-abf7-679671b25e1b', 'bit-hotel': '15385c8c-8c0b-445b-94b5-07fb1c918d4b', 'splinterlands': '98b3ca34-4683-4faf-be40-6814e8fe71b6', 'bullieverse': 'bb978fae-ce1a-4d3c-b18d-223a4ce285ff', 'gunstar-metaverse': '0f9abc34-1d34-46fc-8885-9dd5ed324692', 'gods-unchained': '3df2ee8f-df08-4604-b101-b59e0b3387db'}
    url = f'''https://v3.gamefi.org/api/v1/tokenomics/{listID[name]}?include_statistics=true&include_contracts=true'''
    headers = {
        'Accept': 'application/json'
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response = response.json()
    data = response['data']['items'][0]
    data.pop('id')
    data.pop('icon')

    #Token Utilities
    token_utilities = ""
    
    if not data.get('token_utilities'):
        data['token_utilities'] = { 'blocks': []}
    
    for item in data['token_utilities'].get('blocks', []):
        if item['data'].get('text') is not None:
            token_utilities += item['data']['text'] + '\n'
        if item['data'].get('items') is not None:
            for i in item['data']['items']:
                token_utilities += i + '\n'
    data['token_utilities'] = token_utilities

    # Token economy
    image_url_token_economy = getattr(data, 'token_economy', {}).get('blocks', [])
    if len(image_url_token_economy) > 0:
        image_url_token_economy = image_url_token_economy[0].get('data', {}).get('file', {}).get('url', "")
    data.pop('token_economy')
    token_economy = {
        "image_url": image_url_token_economy,
    }
    data['token_economy'] = token_economy

    # Token distribution
    image_url_token_distribution =getattr(data, 'token_distribution', {}).get('blocks', [])
    if len(image_url_token_distribution) > 0:
        image_url_token_distribution = image_url_token_distribution[0].get('data', {}).get('file', {}).get('url', "")
    data.pop('token_distribution')
    token_distribution = {
        "image_url": image_url_token_distribution,
    }       
    # print("data:", data)                                                                                                                                                                 
    data['token_distribution'] = token_distribution
    # print("data:", data.items())                                                                                                                                                                 


    # Vesting schedule
    image_url_vesting_schedule = getattr(data, 'vesting_schedule', {}).get('blocks', [])
    if len(image_url_vesting_schedule) > 0:
        image_url_vesting_schedule = image_url_vesting_schedule[0].get('data', {}).get('file', {}).get('url', "")
    data.pop('vesting_schedule')
    vesting_schedule = {
        "image_url": image_url_vesting_schedule,
    }
    data['vesting_schedule'] = vesting_schedule

    # Contracts
    for item in data['contracts']:
        item.pop('id')
        
    return {
        "data": data
    }

@alru_cache(maxsize=32, ttl=60**3)
async def get_upcoming_IDO(name, keywords=[]):
    url = "https://ido.gamefi.org/api/v3/pools/upcoming"
    headers = {
        "Accept": "application/json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response = response.json()
    list_project_name = []
    data = response['data']
    for item in data:
        list_project_name.append(item['name'])
        
    global list_ido_game  
    global embedding
    if list_project_name != list_ido_game:
        list_ido_game = list_project_name
        vectordb_docs = chroma_client.get_or_create_collection(
            name="vector_docs", embedding_function=embedding_function, metadata={"hnsw:space": "cosine"})
        vectordb_topic = chroma_client.get_or_create_collection(
            name="vector_topic", embedding_function=embedding_function, metadata={"hnsw:space": "cosine"})
        # Schedule the update functions to run in the background
        asyncio.create_task(update_topic_vector_db(vectordb_topic))
        asyncio.create_task(update_topic_vector_db(vectordb_docs))
        
    overview = {
        "number_of_upcoming_IDO": len(list_project_name),
        "list_project": list_project_name
    }
    return overview    
   

@alru_cache(maxsize=32, ttl=60**3)
async def get_upcoming_IDO_overview(name, keywords=[]):
    url = "https://ido.gamefi.org/api/v3/pools/upcoming"
    headers = {
        "Accept": "application/json",
    }
    description = {
    "slug": "Abbreviation for the project name.",
    "name": "Name of project.",
    "description": "Providing an overview of the project",
    "status": "Status of the IDO, as Preorder, Created,...",
    "claim_policy": "Vesting / includes the vesting period, release rate, and any other provisions regarding the trading freedom of tokens after the IDO.",
    "total_token": "Total number of tokens available for the IDO.",
    "ath": "The maximum return on investment that the project's token has achieved since its all-time high.",
    "whitelist": "The timeframe during which the whitelist is open to receive registrations from individuals who want to participate in the project's IDO.",
    "refund_policy": "The policy regarding refunding funds in case the IDO is unsuccessful or if any issues arise. This information may include the conditions and regulations for requesting a refund, the timeframe, and the process for refunding.",
    "buying_phases": "The time or period during which users can purchase tokens or participate in the project's IDO.",
    "token": {
        "type": "The specific category or standard this token adheres to, defining its functionality and interaction within its respective blockchain ecosystem.",
        "symbol": "The unique identifier or abbreviation for this token, used for trading and referencing in the cryptocurrency markets.",
        "price": "The current market value of the token, often quoted in United States Dollars (USD), which can fluctuate based on supply and demand dynamics.",
        "decimals": "The maximum number of decimal places to which this token can be subdivided, indicating the smallest possible transaction unit for this token."
    },
    "currency": {
        "type": "The unique symbol identifying the currency",
        "decimals": "Defines the smallest unit of the currency that can be handled in transactions."
    },
    "social_networks": "Provide information about the links to the project's social media pages or social media platforms of IDO project.",
    "roadmap": "The project's roadmap, which outlines the key milestones and objectives that the project aims to achieve in the future.",
    "revenue_streams": "Provide information about the sources of income that the project is expected to generate during its operation.",
    "token_utilities": "Provide information about the applications and features that the project's token will provide.",
    "highlights": "Provide information about the unique and standout aspects of the project. This information may include significant achievements, advanced technologies utilized, competitive advantages, market opportunities, or any other strengths that the project aims to highlight to attract the attention of the community and potential investors during the IDO process",
    "launchpad": "The platform or service that is hosting the IDO for the project.",
    "team": "Provide information about the team members and their roles in the project. This information may include the team members' names, positions, experiences, and contributions to the project.",
    "investors_and_partners": "Provide information about the investors and partners that are supporting the project. This information may include the names of the investors and partners, their contributions, and the benefits they bring to the project.",
    "investors": "Provide information about the investors that are supporting the project. This information may include the names of the investors, their contributions, and the benefits they bring to the project.",
    "partners": "Provide information about the partners that are supporting the project. This information may include the names of the partners, their contributions, and the benefits they bring to the project.",
    "business_model": "Provide information about the business model that the project is implementing. This information may include the revenue streams, target markets, value propositions, and other key elements that define the project's business model.",
    "tokenomics": "Provide information about the tokenomics of the project. This information may include the token distribution, token supply, token allocation, token utility, and other key elements that define the project's tokenomics.",
    "total_raise": "The total amount of funds the project aims to raise through the Initial DEX Offering (IDO) process and other funding rounds. This information provides an overview of the level of attractiveness and interest from the community and potential investors towards the project."
    }
    # Some list key to remove
    list_remove_item = ['id', 'game_slug','excerpt', 'banner', 'logo',
        'airdrop_chain_id','display', 'need_kyc', 'featured', 'deployed', 'winner_published',
        'series_content', 'rule', 'box_types', 'sibling','contract_address', 'address_receiver'
    ]
    list_token_remove = [
        'chain_id', 'logo', 'address'
    ]
    # List future
    list_future = ['Business Model', 'Roadmap', 'Tokenomics', 'Revenue Stream', 'Team', 'Token Utilities','Investors and Partners', 'Investors', 'Partners']
    list_key_story ={
        "Business Model": "business_model",
        "Roadmap": "roadmap",
        "Tokenomics": "tokenomics",
        "Revenue Stream": "revenue_streams",
        "Team": "team",
        "Token Utilities": "token_utilities",
        "Investors and Partners": "investors_and_partners",
        "Investors": "investors",
        "Partners": "partners"
    }
    list_key_time = ['from', 'to']

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response = response.json()
    data = response["data"]
    project = {}
    # Take project by name
    for prj in data:
        if prj.get("slug") == name:
            project = prj
            break
    # Remove key of project
    for key in list_remove_item:
        project.pop(key, None)
    # Remove key in token
    for key in list_token_remove:
        project["token"].pop(key, None)
    # Remove key in currency
    for key in list_token_remove:
        project["currency"].pop(key, None)
    # Change time to date
    for key in list_key_time:
        if project['whitelist'].get(key) is not None:
            project['whitelist'][key] = to_date(project['whitelist'][key])
    # Bying phases
    if project.get('buying_phases') is not None:
        for item in project['buying_phases']:
            for key in list_key_time:
                if item.get(key) is not None:
                    item[key] = to_date(item[key])
    # Refund policy
    if project.get('refund_policy') is not None:
        for key in list_key_time:
            if project['refund_policy'].get(key) is not None:
                project['refund_policy'][key] = to_date(project['refund_policy'][key])
    # Cup story
    story = ""
    for item in project['story']['blocks']:
        if item['data'].get('text') is not None:
            if item['data'].get('level') == 1:
                if story != "":
                    is_not_highlight = False
                    for key in list_future:
                        if key in story:
                            project[list_key_story[key]] = story
                            story = ""
                            is_not_highlight = True
                            break
                    # Check highlight
                    if is_not_highlight == False:
                        project['highlights'] = story
                        story = ""
        # Text
        if item['data'].get('text') is not None:
            story += item['data'].get('text') + "\n"
        # Items
        if item['data'].get('items') is not None:
            for i in item['data'].get('items'):
                story += i + "\n"
        # Image url
        if item['data'].get('file') is not None:
            story += item['data']['file'].get('url') + "\n"
    # Pop story
    project.pop('story')
    # Check story
    for future in list_future:
        if future in story:
            project[list_key_story[future]] = story
            story = ""
            break
    # Calculate total raise
    if project['token'].get('price') is None:
        token_price = 0
    else:
        token_price = project['token']['price']   
    total_raise = project['total_token'] * token_price
    project['total_raise'] = total_raise
    # Add description
    overview = {
        "description": description,
        "data": project
    }
    
    if len(keywords) == 0:
        overview = {
            "description": {
                "name" : description['name'],
                "description": description['description'],
                "status": description['status'],
                "token": description['token'],
                "social_networks": description['social_networks'],
            },
            "data": {
                "name" : project['name'],
                "description": project['description'],
                "status": project['status'],
                "token": project['token'],
                "social_networks": project['social_networks'],
            }
        }
    
    return overview


tools_info = [
    {
        "name": "get_infor_overview_gamehub",
        "tool_fn":get_infor_overview_gamehub
    },
    {
        "name": "get_on_chain_performance_gamehub",
        "tool_fn":get_on_chain_performance_gamehub
    },
    {
        "name": "get_community_performance_gamehub",
        "tool_fn":get_community_performance_gamehub
    },
    {
        "name": "get_daily_index_gamehub",
        "tool_fn":get_daily_index_gamehub
    },
    {
        "name": "get_social_score_gamehub",
        "tool_fn":get_social_score_gamehub
    },
    {
        "name": "get_top_backers_gamehub",
        "tool_fn":get_top_backers_gamehub
    },
    {
        "name": "get_infor_overview_ido",
        "tool_fn": get_overview_ido
    },
    {
        "name": "get_tokenomics_gamehub",
        "tool_fn":get_tokenomics_gamehub
    },
    {
        "name": "get_upcoming_IDO",
        "tool_fn":get_upcoming_IDO
    },
    {
        "name": "get_upcoming_IDO_overview",
        "tool_fn":get_upcoming_IDO_overview
    }
]

tools_fn = dict(map(lambda x: (x['name'], x['tool_fn']), tools_info))

async def call_tools_async(feature_dict : dict) -> str:
    # try:
    
        # print(feature_di
        # ct)
    
        topic : dict  = feature_dict["global_topic"]
        content : list = feature_dict["content"]
        
        if topic == '':
            return ""
        
        apis = {
            'social-scores_gamehub' : 'get_social_score_gamehub',
            'daily-index_gamehub' : 'get_daily_index_gamehub',
            'on-chain-performance_gamehub' : 'get_on_chain_performance_gamehub',
            'overview_gamehub' : 'get_infor_overview_gamehub',
            'overview_ido' : 'get_infor_overview_ido',
            # 'team_gamehub' : 'getTeam',
            'community-performance_gamehub' : 'get_community_performance_gamehub',
            'backer_gamehub' : 'get_top_backers_gamehub',
            'tokenomic_gamehub' : 'get_tokenomics_gamehub',
            'overview_list_ido_upcoming': 'get_upcoming_IDO',
            'overview_ido_upcoming': 'get_upcoming_IDO_overview'
        }


        apis_to_call = []
        unique_apis = list(set([c.get('api', "") for c in content]))
        source_dict = {}
        
        for index, c in enumerate(content):
            if c.get('api', "") == "":
                continue
            # print(c.get('api', ""))
            if c['api'] not in source_dict:
                source_dict[c['api']] = []
            
            source_dict[c['api']].append(c.get('source', ""))
            source_dict[c['api']] = list(set(source_dict[c['api']]))
        
        for api in unique_apis:
            if api == "":
                continue
            apis_to_call.append({
                'api' : apis.get(api, ""),
                'source' : source_dict[api],
            })

        context = ""

        tasks = []
        
        if topic.get('type', '') == "topic" and len(content) == 0:
            tasks.append(tools_fn[apis[topic['api']]](topic['source']))
            result = await asyncio.gather(*tasks) 
            result = result[0]
            info = result
            # if 'data' in result:
            #     if 'introduction' in result['data']:
            #         info = str(result['data']['introduction']) 
            #     elif 'description' in result['data']:
            #         info = str(result['data']['description']) 
            
            context = f'''\nGeneral information of {topic['source']}:\n{info}\n'''
            
            return context     
            
        list_rs = []
        for api in apis_to_call:
            if api['api'] == "":
                continue
            tasks.append({
                'api': api['api'],
                'param': topic['source'],
                'keywords':api['source']
                }
            )
            # print(api['source'])
            list_rs.append(f'''\nInformation of {topic['source']} about {", ".join(api['source'])}:\n''')

        tasks = list(map(lambda x: tools_fn[x['api']](x['param'], tuple(x['keywords'])), tasks))
        # tasks = list(map(lambda x: tools_fn[x['api']](x['param']), tasks))
        results = await asyncio.gather(*tasks)
        for index, result in enumerate(results): 
            context += f'''{list_rs[index]}{result}\n'''
        return context
    # except Exception as e:
    #     print("Error:",e)
    #     return ""
