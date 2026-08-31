"""
cache_manager.py
-----------------
Demonstrates both LangChain cache backends and lets the UI switch between
them at runtime.

InMemoryCache:
    - Lives entirely in RAM, fastest possible cache hit.
    - Cleared when the Python process restarts.

SQLiteCache:
    - Backed by a real .db file on disk.
    - Slightly slower than pure RAM but persists across app restarts.

Both work the same way once registered: call set_llm_cache(cache) and
LangChain automatically checks the cache before every model call, keyed
on a hash of (prompt, model, params). Repeating the same request is
faster and makes no new (billed) API call.
"""

from langchain.globals import set_llm_cache
from langchain_community.cache import InMemoryCache, SQLiteCache

from src.config import SQLITE_CACHE_PATH

_active_cache_name = "No caching"


def enable_in_memory_cache():
    global _active_cache_name
    set_llm_cache(InMemoryCache())
    _active_cache_name = "In-Memory Cache"


def enable_sqlite_cache(db_path: str = SQLITE_CACHE_PATH):
    global _active_cache_name
    set_llm_cache(SQLiteCache(database_path=db_path))
    _active_cache_name = "SQLite Cache"


def disable_cache():
    global _active_cache_name
    set_llm_cache(None)
    _active_cache_name = "No caching"


def set_cache_mode(mode: str):
    """Single entry point used by the Streamlit sidebar selectbox."""
    if mode == "In-Memory Cache":
        enable_in_memory_cache()
    elif mode == "SQLite Cache":
        enable_sqlite_cache()
    else:
        disable_cache()
    return _active_cache_name


def get_active_cache_name() -> str:
    return _active_cache_name
