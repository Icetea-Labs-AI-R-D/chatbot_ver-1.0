def get_price(usage: dict):
    total_tokens = usage.get.prompt_tokens + 3 * usage.completion_tokens
    return 0.5 * total_tokens / 1000000