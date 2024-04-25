from functools import lru_cache, wraps
from datetime import datetime, timedelta, timezone

def timed_lru_cache(seconds: int, maxsize: int = 128):
    def wrapper_cache(func):
        func = lru_cache(maxsize=maxsize)(func)
        func.lifetime = timedelta(seconds=seconds)
        func.expires = datetime.now(timezone.utc) + func.lifetime
        
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if datetime.now(timezone.utc) >= func.expires:
                func.cache_clear()
                func.expires = datetime.now(timezone.utc) + func.lifetime
            return func(*args, **kwargs)
        
        return wrapped_func
    return wrapper_cache