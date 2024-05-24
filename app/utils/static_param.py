async def many_requests_generator():
    return b"Too many requests, please try again later."


async def new_conversation_generator(n: int = 1):
    content = [
        f"✅ **Starting new dialog due to timeout** \n\n",
        f"**Hey there! I'm Gamefi.org GPT, your helpful AI bot for anything Games and IDO projects available on the Gamefi.org platform.  How can I assist you today**? \n\n",
    ]

    n = min(n, len(content))   

    for i in range(n):
        yield content[i].encode()