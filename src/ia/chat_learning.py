import json, os, time, threading, random, re
from collections import defaultdict
from src import PROJECT_ROOT

LEARN_FILE = os.path.join(PROJECT_ROOT, "data", "chat_learning.json")

POSITIVE_EMOTES = [
    "PogChamp", "Kreygasm", "EZ", "Clap", "OMEGALUL",
    "LUL", "KEKW", "Pog", "PogU", "HYPERS",
    "FeelsGoodMan", "Sadge", "Okayge", "WICKED",
    "jaja", "lol", "xd", ":", "❤", "🔥", "💯", "👏",
]

NEGATIVE_EMOTES = [
    "ResidentSleeper", "NotLikeThis", "DansGame",
    "WutFace", "monkaS", "FeelsBadMan", "PepeLaugh",
    "KKona", "MingLee", "🖕", "👎", "😴", "💤",
]

# Palabras clave que indican que el chat reacciona a Karin
REACTION_KEYWORDS = [
    "Karin", "bien", "mal", "gracioso", "aburrido",
    "genial", "tonto", "sabia", "feo", "bonito",
]

POSITIVE_WORDS = ["bien", "genial", "gracioso", "mejor", "bueno", "sabia", "bonito", "divertido", "increible", "epico"]
NEGATIVE_WORDS = ["mal", "aburrido", "tonto", "feo", "malo", "horrible", "pesado", "molesto", "cringe", "penoso"]

class ChatLearning:
    def __init__(self):
        self.data = self._load()
        self._lock = threading.RLock()
        self._pending_save = False
        self._recent_responses = {}

    def _load(self):
        try:
            if os.path.exists(LEARN_FILE):
                with open(LEARN_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "patterns" not in data:
                        data["patterns"] = {}
                    if "responses" not in data:
                        data["responses"] = {}
                    if "stats" not in data:
                        data["stats"] = {"total_positive": 0, "total_negative": 0, "total_neutral": 0}
                    if "avoid_topics" not in data:
                        data["avoid_topics"] = []
                    if "preferred_topics" not in data:
                        data["preferred_topics"] = []
                    return data
        except Exception:
            pass
        return {"patterns": {}, "responses": {}, "stats": {"total_positive": 0, "total_negative": 0, "total_neutral": 0}, "avoid_topics": [], "preferred_topics": []}

    def _save(self):
        with self._lock:
            try:
                with open(LEARN_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    def _delayed_save(self):
        if self._pending_save:
            return
        self._pending_save = True
        def _save_later():
            time.sleep(3)
            self._save()
            self._pending_save = False
        threading.Thread(target=_save_later, daemon=True).start()

    def analyze_reaction(self, chat_message, last_ai_response=None):
        msg_lower = chat_message.lower()
        reaction = {"emotion": 0, "is_reaction": False, "intensity": 0}

        has_positive_emote = any(e.lower() in msg_lower for e in POSITIVE_EMOTES)
        has_negative_emote = any(e.lower() in msg_lower for e in NEGATIVE_EMOTES)
        has_positive_word = any(w in msg_lower for w in POSITIVE_WORDS)
        has_negative_word = any(w in msg_lower for w in NEGATIVE_WORDS)

        if last_ai_response:
            resp_keywords = last_ai_response.lower().split()[:10]
            is_about_karin = any(k.lower() in msg_lower for k in ["karin", "ella", "dijo", "la ia"])
            mentions_ai = any(k in msg_lower for k in REACTION_KEYWORDS)
            reaction["is_reaction"] = is_about_karin or mentions_ai

        if has_positive_emote or has_positive_word:
            reaction["emotion"] = 1  # positive
            reaction["intensity"] = (1 if has_positive_word else 0) + (2 if has_positive_emote else 0)
        elif has_negative_emote or has_negative_word:
            reaction["emotion"] = -1  # negative
            reaction["intensity"] = (1 if has_negative_word else 0) + (2 if has_negative_emote else 0)

        if reaction["emotion"] != 0 and reaction["intensity"] > 0:
            with self._lock:
                if reaction["emotion"] == 1:
                    self.data["stats"]["total_positive"] += reaction["intensity"]
                elif reaction["emotion"] == -1:
                    self.data["stats"]["total_negative"] += reaction["intensity"]
            self._delayed_save()

        return reaction

    def track_response(self, response_id, text):
        self._recent_responses[response_id] = {
            "text": text,
            "time": time.time(),
            "reactions": []
        }
        if len(self._recent_responses) > 50:
            oldest = min(self._recent_responses.keys(), key=lambda k: self._recent_responses[k]["time"])
            del self._recent_responses[oldest]

    def record_reaction_to_response(self, response_id, user, chat_message, reaction):
        if response_id not in self._recent_responses:
            return
        self._recent_responses[response_id]["reactions"].append({
            "user": user,
            "message": chat_message,
            "reaction": reaction,
            "time": time.time()
        })

    def learn_pattern(self, ai_response, chat_reaction):
        if not ai_response or chat_reaction.get("emotion") == 0:
            return
        with self._lock:
            pattern = self._extract_pattern(ai_response)
            if not pattern:
                return
            if pattern not in self.data["patterns"]:
                self.data["patterns"][pattern] = {"count": 0, "positive": 0, "negative": 0}
            self.data["patterns"][pattern]["count"] += 1
            if chat_reaction["emotion"] == 1:
                self.data["patterns"][pattern]["positive"] += 1
            elif chat_reaction["emotion"] == -1:
                self.data["patterns"][pattern]["negative"] += 1
        self._delayed_save()

    def _extract_pattern(self, text):
        text = text.lower().strip()
        text = re.sub(r'[^\w\sáéíóúñ]', '', text)
        words = text.split()
        if len(words) < 3:
            return None
        return " ".join(words[:5])

    def get_style_adjustment(self):
        with self._lock:
            total_p = self.data["stats"]["total_positive"]
            total_n = self.data["stats"]["total_negative"]
            total = total_p + total_n
            if total < 10:
                return {}  # Not enough data yet

            ratio = total_p / max(total, 1)
            adj = {}

            # Ajustes de estilo según feedback
            if ratio > 0.7:
                adj["tone"] = "confiado"
                adj["energy"] = "alta"
                adj["extra_instruction"] = "El chat disfruta tus comentarios. Sigue asi, con energia y confianza."
            elif ratio > 0.5:
                adj["tone"] = "normal"
                adj["energy"] = "media"
                adj["extra_instruction"] = ""
            elif ratio > 0.3:
                adj["tone"] = "cauteloso"
                adj["energy"] = "baja"
                adj["extra_instruction"] = "El chat parece no reaccionar muy bien. Intenta ser mas natural y menos intensa."
            else:
                adj["tone"] = "reservado"
                adj["energy"] = "baja"
                adj["extra_instruction"] = "El chat no esta respondiendo bien. Se mas neutral y observa que funciona."

            # Identificar patrones que funcionan bien
            good_patterns = []
            bad_patterns = []
            for pattern, info in self.data["patterns"].items():
                if info["count"] >= 3:
                    success = info["positive"] / max(info["count"], 1)
                    if success > 0.6:
                        good_patterns.append(pattern)
                    elif success < 0.3:
                        bad_patterns.append(pattern)

            adj["good_patterns"] = good_patterns[:5]
            adj["avoid_patterns"] = bad_patterns[:5]

            if good_patterns:
                adj["extra_instruction"] = (adj.get("extra_instruction", "") +
                    f" Al chat le gusta cuando hablas de: {', '.join(good_patterns[:3])}.")
            if bad_patterns:
                adj["extra_instruction"] = (adj.get("extra_instruction", "") +
                    f" Evita hablar de: {', '.join(bad_patterns[:2])}.")

            return adj

    def get_stats(self):
        with self._lock:
            return dict(self.data["stats"])

    def clear(self):
        with self._lock:
            self.data = {"patterns": {}, "responses": {}, "stats": {"total_positive": 0, "total_negative": 0, "total_neutral": 0}, "avoid_topics": [], "preferred_topics": []}
            self._recent_responses = {}
            self._save()

    def get_learning_summary(self):
        stats = self.get_stats()
        total = stats["total_positive"] + stats["total_negative"]
        if total == 0:
            return "Aún no hay suficientes datos de aprendizaje."
        ratio = (stats["total_positive"] / total) * 100
        return f"Feedback: {ratio:.0f}% positivo ({stats['total_positive']}👍 / {stats['total_negative']}👎) de {total} reacciones"


_default_learning = None

def get_chat_learning():
    global _default_learning
    if _default_learning is None:
        _default_learning = ChatLearning()
    return _default_learning

def analyze_reaction(chat_message, last_ai_response=None):
    return get_chat_learning().analyze_reaction(chat_message, last_ai_response)

def get_style_adjustment():
    return get_chat_learning().get_style_adjustment()

def get_learning_stats():
    return get_chat_learning().get_stats()

def get_learning_summary():
    return get_chat_learning().get_learning_summary()
