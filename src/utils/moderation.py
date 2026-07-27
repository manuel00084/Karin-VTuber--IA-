import os, json, re
from src import PROJECT_ROOT
from src.utils.log import error

DATA_FILE = os.path.join(PROJECT_ROOT, "data", "moderacion.json")

DEFAULT_ACTION = "log"  # log | delete | timeout

def _load():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"default_action": DEFAULT_ACTION, "words": [], "timeout_seconds": 60}
    return {"default_action": DEFAULT_ACTION, "words": [], "timeout_seconds": 60}

def _save(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_words():
    return _load()["words"]

def add_word(word, action=None):
    data = _load()
    word_lower = word.lower().strip()
    for w in data["words"]:
        if w["word"] == word_lower:
            w["action"] = action or data["default_action"]
            _save(data)
            return
    data["words"].append({"word": word_lower, "action": action or data["default_action"]})
    _save(data)

def remove_word(word):
    data = _load()
    word_lower = word.lower().strip()
    data["words"] = [w for w in data["words"] if w["word"] != word_lower]
    _save(data)

def get_default_action():
    return _load()["default_action"]

def set_default_action(action):
    data = _load()
    data["default_action"] = action
    _save(data)

def get_timeout_seconds():
    return _load()["timeout_seconds"]

def set_timeout_seconds(secs):
    data = _load()
    data["timeout_seconds"] = max(1, int(secs))
    _save(data)

def check_message(text):
    data = _load()
    text_lower = text.lower().strip()
    for w in data["words"]:
        pattern = re.compile(r'\b' + re.escape(w["word"]) + r'\b', re.IGNORECASE)
        if pattern.search(text_lower):
            action = w.get("action", data["default_action"])
            return {"word": w["word"], "action": action}
    return None
