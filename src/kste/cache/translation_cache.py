import json, os, time, hashlib, threading
from src import PROJECT_ROOT
from src.utils.log import info, error
from src.kste.config.kste_config import KSTEConfig

_CACHE_DIR = os.path.join(PROJECT_ROOT, "data")
_CACHE_PATH = os.path.join(_CACHE_DIR, "kste_cache.json")


class TranslationCache:
    def __init__(self, config):
        self.config = config
        self._cache = {}
        self._lock = threading.Lock()
        self.load()

    def get(self, text, source, target):
        if not text:
            return None
        k = self._hash(text, source, target)
        with self._lock:
            entry = self._cache.get(k)
            if entry is None:
                return None
            age_days = (time.time() - entry.get("ts", 0)) / 86400
            if age_days > self.config.cache_ttl_days:
                del self._cache[k]
                return None
            entry["hits"] = entry.get("hits", 0) + 1
            return entry.get("translation")

    def set(self, text, source, target, translation):
        if not text or not translation:
            return
        k = self._hash(text, source, target)
        with self._lock:
            if len(self._cache) >= self.config.cache_max_entries:
                self._evict_oldest()
            self._cache[k] = {
                "translation": translation,
                "ts": time.time(),
                "hits": 0,
            }

    def _hash(self, text, source, target):
        raw = f"{source}:{target}:{text.strip().lower()}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _evict_oldest(self):
        if not self._cache:
            return
        oldest_key = min(self._cache, key=lambda k: self._cache[k].get("ts", 0))
        del self._cache[oldest_key]

    def clear(self):
        with self._lock:
            self._cache.clear()

    def load(self):
        try:
            if os.path.exists(_CACHE_PATH):
                with open(_CACHE_PATH, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                info(f"KSTE cache loaded: {len(self._cache)} entries")
        except Exception as e:
            error(f"KSTE cache load: {e}")
            self._cache = {}

    def save(self):
        try:
            os.makedirs(_CACHE_DIR, exist_ok=True)
            with open(_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False)
            info(f"KSTE cache saved: {len(self._cache)} entries")
        except Exception as e:
            error(f"KSTE cache save: {e}")

    def size(self):
        return len(self._cache)
