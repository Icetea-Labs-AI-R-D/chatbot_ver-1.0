import requests
import json
import asyncio

def get_infor_overview_gamehub(name):
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
    response = requests.get(url, headers).json()
    # print(response)
    gameId = response['data']['item'].get('id', "")
    nameGame = response['data']['item'].get('name', "")
    status = response['data']['item'].get('status', "")
    published_at = response['data']['item'].get('published_at', "")
    white_paper = response['data']['item'].get('white_paper', "")
    banners = response['data']['item'].get('banners', "")
    introduction = response['data']['item'].get('introduction', "")
    roadmap_text = response['data']['item'].get('roadmap_text', "")
    play_mode = response['data']['item'].get('play_mode', "")
    play_to_earn_model = response['data']['item'].get('play_to_earn_model', "")
    links = response['data']['item'].get('links', "")
    ratingScore = response['data']['metadata'].get('counts', {}).get(gameId, "")
    tokenomicsCompact = response['data']['item'].get('tokenomics_compact', "")
    studios = response['data']['item'].get('studios', "")
    studios = [studio['name'] for studio in studios]
    
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
            "tokenomics-compact": tokenomicsCompact,
            "studios": studios
        },
        "description": description
    }
    print(overview)
    return overview

def get_on_chain_performance_gamehub(name):
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
    response = requests.get(url, headers).json()
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
    print(res)
    return res

def get_community_performance_gamehub(name):
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
    response = requests.get(url, headers).json()
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
    print(res)
    return res

def get_daily_index_gamehub(name):
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
    reponse = requests.get(url, headers).json()
    try:
        data = reponse['data']
    except:
        data = {}
        description = {}
    print(data)
    return {
        "data": data,
        "description": description
    }
    
def get_social_score_gamehub(name):
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
    response = requests.get(url,headers).json()
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
    print(res)
    return res

def get_top_backers_gamehub(name):
    """Get all backers of a game from GameFi API."""
    
    url = f'''https://v3.gamefi.org/api/v1/games/{name}/top-backers'''
    headers = {
        'Accept': 'application/json'
    }
    reponse = requests.get(url,headers).json()
    listBacker = []
    try:
        items = reponse['data']['items']
        for index, item in enumerate(items):
            name = reponse['data']['items'][index]['name']
            linkWebsite = reponse['data']['items'][index]['links']['website']
            listBacker.append(
                {
                    "name": name,
                    "link-website": linkWebsite 
                }
            )
    except:
        listBacker = []
    backers = {
        "data": listBacker
    }
    print(backers)
    return backers

import requests
import json
from datetime import datetime, timezone

def to_date(time):
    return str(datetime.fromtimestamp(time, timezone.utc))
def get_overview_ido(name):
    url = f'''https://ido.gamefi.org/api/v3/pool/{name}'''
    headers = {
        'Accept': 'application/json'
    }
    reponse = requests.get(url, headers).json()
    # Remove key in data
    data = reponse['data']
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
    
    overview = {
        "description": description,
        "data": data
    }
    print(overview)
    return overview

listID = {'mobox': 'cda1dd30-0128-4ffe-bb65-29001e1ad0e9', 'the-sandbox': '08c1027f-4984-487a-a968-3c710ef2bd00', 'binaryx': '9e2def2a-f701-4721-a2c7-925b83018adf', 'axie-infinity': 'f96d0db8-d551-40c3-905c-e6e002c920e3', 'x-world-games': 'ffb52c78-016e-44f1-bfea-b57286d91898', 'thetan-arena': '149b050a-f391-4397-8dc0-163ea2e14138', 'alien-worlds': '0c49e040-be09-40ee-a178-e77bf404796e', 'league-of-kingdoms': '5293cb42-c26e-4a32-b80e-f595adc07083', 'burgercities': 'b91204b9-4197-4e4a-b5c7-56343ef49141', 'kryptomon': '0b54a231-070a-4474-ad6e-a17afba9a6c6', 'wanaka-farm': '466a5862-7e68-467b-85ef-cb677f5e96c5', 'sidus-heroes': '04054d55-b1ec-4234-9f10-c789b3b56065', 'ninneko': 'd2f84664-d28d-4729-8a0a-0ed33c39c521', 'cryptoblades': 'ad82204a-23d5-4ffe-a1ae-f8fb1f71b5f7', 'ultimate-champions': 'a1ee2386-33de-47cc-a3fe-11d0342de2e9', 'monsterra': 'b0b1271c-7b48-4bdc-a555-6ce95fc8bdfe', 'polychain-monsters': '47e03d0d-c353-47b0-b99c-a2a82dd875ae', 'iguverse': 'a47d016f-76e8-4f9c-819d-7c81daad7e91', 'heroes-empires': '79075231-aa7d-4b52-97d5-4390521f108b', 'illuvium': 'd3bf9ecf-58f1-488d-a3dc-8bead33eb930', 'xana': '3a0e8a04-255b-435b-856c-0723c01f08db', 'aqua-farm': '9a6373c8-9c46-40b5-9d23-c4fcbe873b20', 'mines-of-dalarnia': '60424918-41f0-4334-9ce3-2671f1febe88', 'magiccraft': 'a3110df8-f298-483c-aa0b-ce4fcae44841', 'derace': '31dcd5f2-5293-4db4-abf7-679671b25e1b', 'bit-hotel': '15385c8c-8c0b-445b-94b5-07fb1c918d4b', 'splinterlands': '98b3ca34-4683-4faf-be40-6814e8fe71b6', 'bullieverse': 'bb978fae-ce1a-4d3c-b18d-223a4ce285ff', 'gunstar-metaverse': '0f9abc34-1d34-46fc-8885-9dd5ed324692', 'gods-unchained': '3df2ee8f-df08-4604-b101-b59e0b3387db'}

def get_tokenomics_gamehub(name):
    url = f'''https://v3.gamefi.org/api/v1/tokenomics/{listID[name]}?include_statistics=true&include_contracts=true'''
    headers = {
        'Accept': 'application/json'
    }
    reponse = requests.get(url, headers).json()
    data = reponse['data']['items'][0]
    data.pop('id')
    data.pop('icon')

    #Token Utilities
    token_utilities = ""
    for item in data['token_utilities']['blocks']:
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
        
    print(data)
    return data


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
    }
]
tools_fn = dict(map(lambda x: (x['name'], x['tool_fn']), tools_info))
def call_tools_sync(feature_dict : dict) -> str:
    # try:
        topic : dict  = feature_dict["topic"]
        content : list = feature_dict["content"]
        
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
        }
        #TODO check whether the topic is a gamehub or ido game name


        tool_index_dict = {}
        # print(content)
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
        
        if topic['type'] == "topic" and len(content) == 0:
            result = tools_fn['get_infor_overview_' + topic['topic']](topic['source'])           
            # print(result)
            info = ""
            if 'introduction' in result['data']:
                info = result['data']['introduction']
            elif 'description' in result['data']:
                info = result['data']['description']
            
            context = f'''\nGeneral information of {topic['source']}:\n{info}\n'''
            
            return context     
            
        for api in apis_to_call:
            if api['api'] == "":
                continue
            print("Call api:", api['api'])
            result = ""
            result = tools_fn[api['api']](topic['source'])
            context += f'''\nInformation of {topic['source']} about {", ".join(api['source'])}:\n{result}\n'''
        
        # print(context)  
        return context
    # except Exception as e:
    #     print("Error:",e)
    #     return ""