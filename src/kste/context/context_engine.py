import re
from src.kste.parser.message_parser import ChatChannel
from src.kste.dictionary.game_dictionary import GameDictionary


class ContextEngine:
    def __init__(self, dictionary):
        self._dictionary = dictionary

    def resolve(self, message, player_profile):
        text = message.texto
        words = text.split()
        resolved = []
        for word in words:
            clean = re.sub(r'[^\w]', '', word)
            upper = clean.upper()
            meaning = self._dictionary.resolve_acronym(upper, message.canal)
            if meaning:
                resolved.append(meaning)
            else:
                resolved.append(word)
        message.texto = " ".join(resolved)
        return message

    def _build_context_window(self, player, memory, n=10):
        if memory is None:
            return []
        try:
            recent = memory.get_recent(player, n=n)
            return [m.texto for m in recent]
        except Exception:
            return []
