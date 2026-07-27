import re
from src.kste.parser.message_parser import ChatChannel


_MMORPG_EN = {
    "DPS": "Damage Per Second",
    "HP": "Health Points",
    "MP": "Magic Points",
    "AOE": "Area of Effect",
    "NPC": "Non-Player Character",
    "PVP": "Player vs Player",
    "PVE": "Player vs Environment",
    "GG": "Good Game",
    "LFG": "Looking for Group",
    "LFP": "Looking for Party",
    "BRB": "Be Right Back",
    "AFK": "Away from Keyboard",
    "OTW": "On The Way",
    "TY": "Thank You",
    "GLHF": "Good Luck Have Fun",
    "OOM": "Out of Mana",
    "DOT": "Damage Over Time",
    "HOT": "Heal Over Time",
    "CC": "Crowd Control",
    "CD": "Cooldown",
    "WTS": "Want to Sell",
    "WTB": "Want to Buy",
    "WTT": "Want to Trade",
    "LMAO": "Laughing My Ass Off",
    "LOL": "Laugh Out Loud",
    "OMG": "Oh My God",
    "IDK": "I Don't Know",
    "TBH": "To Be Honest",
    "IMO": "In My Opinion",
    "AFK": "Away From Keyboard",
}

_MMORPG_JA = {
    "PT": "Party",
    "GT": "Guild Talk",
    "JP": "Job Point",
    "FF": "Final Fantasy",
    "RMT": "Real Money Trade",
}

_MMORPG_KO = {
    "파티": "Party",
    "길드": "Guild",
    "던전": "Dungeon",
    "레이드": "Raid",
    "버프": "Buff",
    "디버프": "Debuff",
}

_MMORPG_PT = {
    "TBM": "Também",
    "VLW": "Valeu",
    "FT": "Forte",
    "PJ": "Personagem",
    "HP": "Pontos de Vida",
    "MP": "Pontos de Magia",
}

_ACRONYMS_BY_CHANNEL = {
    ChatChannel.PARTY: {
        "ET": "Endless Tower",
        "DF": "Dungeon Finder",
        "R": "Raid",
        "PVP": "Player vs Player",
        "BOSS": "Boss",
    },
    ChatChannel.TRADE: {
        "ET": "Ethereal Tear",
        "RMS": "Rainbow Moon Stone",
        "WTS": "Want to Sell",
        "WTB": "Want to Buy",
        "WTT": "Want to Trade",
        "COD": "Cash on Delivery",
    },
    ChatChannel.GUILD: {
        "ET": "Event Tonight",
        "GT": "Guild Talk",
        "GA": "Guild Activity",
        "GR": "Guild Raid",
    },
    ChatChannel.GENERAL: {
        "ET": "Endless Tower",
        "GG": "Good Game",
        "HF": "Have Fun",
        "GL": "Good Luck",
    },
}

_EMOTICON_MAP = {
    ":)": "sonrisa",
    ":(": "tristeza",
    ":D": "feliz",
    ";)": "guiño",
    "<3": "corazón",
    "XD": "risa",
    "T_T": "llorando",
    "o/": "saludo",
    ":P": "bromista",
    ":O": "sorpresa",
    "^^": "alegría",
    ":3": "tierno",
    "B)": "lentes",
    "xD": "risa",
    ":'(": "llorando feliz",
}

_ALL_GLOSSARY = {}
_ALL_GLOSSARY.update(_MMORPG_EN)
_ALL_GLOSSARY.update(_MMORPG_JA)
_ALL_GLOSSARY.update(_MMORPG_KO)
_ALL_GLOSSARY.update(_MMORPG_PT)


class GameDictionary:
    def __init__(self):
        self._custom = {}

    def lookup(self, text, language):
        protected_tokens = []
        result = text
        for term, meaning in _ALL_GLOSSARY.items():
            pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            if pattern.search(result):
                protected_tokens.append(term)
                result = pattern.sub(f"«{term}»", result)
        for emoticon, replacement in _EMOTICON_MAP.items():
            if emoticon in result:
                result = result.replace(emoticon, replacement)
        for term, meaning in self._custom.items():
            pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            if pattern.search(result):
                protected_tokens.append(term)
                result = pattern.sub(f"«{term}»", result)
        return result, protected_tokens

    def resolve_acronym(self, acronym, channel):
        channel_map = _ACRONYMS_BY_CHANNEL.get(channel, {})
        if acronym in channel_map:
            return channel_map[acronym]
        if acronym in _ALL_GLOSSARY:
            return _ALL_GLOSSARY[acronym]
        return None

    def reverse_lookup(self, text, target_lang):
        return text

    def add_term(self, term, meaning, lang="en"):
        self._custom[term] = meaning

    def remove_term(self, term):
        self._custom.pop(term, None)

    def load_custom(self, path):
        try:
            import json
            with open(path, "r", encoding="utf-8") as f:
                self._custom.update(json.load(f))
        except Exception:
            pass
