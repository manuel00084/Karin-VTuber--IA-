import json, os
from dataclasses import dataclass, field
from src import PROJECT_ROOT
from src.utils.log import warn

_QUICK_REPLIES_DIR = os.path.join(os.path.dirname(__file__), "..", "quick_replies")


@dataclass
class QuickReply:
    texto_es: str
    traducciones: dict = field(default_factory=dict)
    categoria: str = ""


class QuickReplyManager:
    _CATEGORIES = {
        "greetings": {"icon": "👋", "label": "Saludos"},
        "party": {"icon": "⚔️", "label": "Party"},
        "guild": {"icon": "🏰", "label": "Guild"},
        "trade": {"icon": "💰", "label": "Comercio"},
        "help": {"icon": "❓", "label": "Ayuda"},
        "farewell": {"icon": "👋", "label": "Despedidas"},
    }

    def __init__(self, quick_replies_dir=None):
        self._dir = quick_replies_dir or os.path.normpath(_QUICK_REPLIES_DIR)
        self._cache = {}

    def get_categories(self):
        return dict(self._CATEGORIES)

    def get_replies(self, category):
        if category in self._cache:
            return self._cache[category]
        replies = self._load_category(category)
        self._cache[category] = replies
        return replies

    def get_reply_text(self, category, index, target_lang):
        replies = self.get_replies(category)
        if 0 <= index < len(replies):
            reply = replies[index]
            return reply.traducciones.get(target_lang, reply.texto_es)
        return ""

    def get_all_texts(self, category, target_lang):
        replies = self.get_replies(category)
        return [r.traducciones.get(target_lang, r.texto_es) for r in replies]

    def _load_category(self, category):
        path = os.path.join(self._dir, f"{category}.json")
        replies = []
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for es_text, translations in data.items():
                    replies.append(QuickReply(
                        texto_es=es_text,
                        traducciones=translations,
                        categoria=category
                    ))
        except Exception as e:
            warn(f"KSTE quick_reply load error [{category}]: {e}")
        return replies

    def add_custom_reply(self, category, texto_es, traducciones):
        replies = self.get_replies(category)
        replies.append(QuickReply(
            texto_es=texto_es,
            traducciones=traducciones,
            categoria=category
        ))
        self._cache[category] = replies
        self._save_category(category, replies)

    def _save_category(self, category, replies):
        path = os.path.join(self._dir, f"{category}.json")
        data = {}
        for r in replies:
            data[r.texto_es] = r.traducciones
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            warn(f"KSTE quick_reply save error: {e}")

    def reload(self):
        self._cache.clear()
