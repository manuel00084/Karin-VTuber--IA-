import time
import threading
import hashlib
from collections import OrderedDict


class AIResponseCache:
    """LRU cache for AI responses. Keyed by (user, text, prompt) hash."""

    def __init__(self, maxsize=50, ttl=60):
        self._maxsize = maxsize
        self._ttl = ttl
        self._cache = OrderedDict()
        self._lock = threading.Lock()

    def _make_key(self, user, text, prompt):
        raw = f"{user}:{text.strip().lower()}:{prompt.strip()}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, user, text, prompt):
        key = self._make_key(user, text, prompt)
        with self._lock:
            entry = self._cache.get(key)
            if entry and (time.time() - entry["time"]) < self._ttl:
                self._cache.move_to_end(key)
                return entry["response"]
            if entry:
                del self._cache[key]
            return None

    def set(self, user, text, prompt, response):
        if not response or response.startswith("⚠"):
            return
        key = self._make_key(user, text, prompt)
        with self._lock:
            self._cache[key] = {"response": response, "time": time.time()}
            if len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)

    def clear(self):
        with self._lock:
            self._cache.clear()

    @property
    def size(self):
        with self._lock:
            return len(self._cache)


_ai_cache = AIResponseCache()


def get_ai_cache():
    return _ai_cache


def cached_ask_ai(user, text, api_key, prompt, provider="groq", **kwargs):
    cache = get_ai_cache()
    cached = cache.get(user, text, prompt)
    if cached:
        return cached
    from src.ia import ask_ai
    response = ask_ai(text, api_key, prompt, provider=provider, **kwargs)
    cache.set(user, text, prompt, response)
    return response


def clear_ai_cache():
    get_ai_cache().clear()
