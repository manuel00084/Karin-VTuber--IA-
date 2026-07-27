import json, os, time, hashlib
from src import PROJECT_ROOT
from src.utils.log import error

class TranslationMemory:
    def __init__(self, max_size=5000):
        self._cache = {}
        self._max_size = max_size
        self._path = os.path.join(PROJECT_ROOT, "data", "translation_memory.json")
        self._dict_path = os.path.join(PROJECT_ROOT, "data", "user_dictionary.json")
        self._user_dict = {}
        self._load()
        self._load_dict()

    def _load(self):
        try:
            if os.path.exists(self._path):
                with open(self._path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
        except Exception:
            self._cache = {}

    def _save(self):
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            error(f"TranslationMemory._save: {e}")

    def _load_dict(self):
        try:
            if os.path.exists(self._dict_path):
                with open(self._dict_path, "r", encoding="utf-8") as f:
                    self._user_dict = json.load(f)
        except Exception:
            self._user_dict = {}

    def _save_dict(self):
        try:
            with open(self._dict_path, "w", encoding="utf-8") as f:
                json.dump(self._user_dict, f, ensure_ascii=False, indent=2)
        except Exception as e:
            error(f"TranslationMemory._save_dict: {e}")

    def _key(self, text, source, target):
        raw = f"{source}:{target}:{text.strip().lower()}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, text, source, target):
        k = self._key(text, source, target)
        entry = self._cache.get(k)
        if entry and time.time() - entry.get("ts", 0) < 86400 * 30:
            dict_match = self._check_dict(text)
            if dict_match:
                return dict_match
            return entry.get("translation")
        return None

    def set(self, text, source, target, translation):
        if not text or not translation:
            return
        k = self._key(text, source, target)
        if len(self._cache) >= self._max_size:
            oldest = min(self._cache.keys(), key=lambda x: self._cache[x].get("ts", 0))
            del self._cache[oldest]
        self._cache[k] = {"translation": translation, "ts": time.time()}
        self._save()

    def _check_dict(self, text):
        tl = text.strip().lower()
        for pattern, replacement in self._user_dict.items():
            if pattern.lower() in tl:
                return replacement
        return None

    def add_dict_entry(self, source_text, translation):
        if source_text and translation:
            self._user_dict[source_text.strip()] = translation.strip()
            self._save_dict()

    def remove_dict_entry(self, source_text):
        self._user_dict.pop(source_text.strip(), None)
        self._save_dict()

    def get_dict(self):
        return dict(self._user_dict)

    def clear(self):
        self._cache.clear()
        self._save()
