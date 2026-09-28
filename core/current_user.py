from functools import lru_cache

CURRENT_USER_ID: int = 1


@lru_cache(maxsize=1)
def get_current_user_id() -> int:
    return CURRENT_USER_ID
