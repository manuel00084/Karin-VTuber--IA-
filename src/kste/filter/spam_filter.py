import re
import time
from collections import deque
from src.kste.parser.message_parser import ChatMessage

_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "]+",
    flags=re.UNICODE
)

_SPAM_PATTERNS = [
    re.compile(r'(.)\1{5,}'),
    re.compile(r'[!¡]{4,}'),
    re.compile(r'[?¿]{4,}'),
    re.compile(r'\d{6,}'),
    re.compile(r'(https?://\S+)', re.IGNORECASE),
    re.compile(r'\b(buy|sell|gold|coin|item|price|cheap|discount)\b', re.IGNORECASE),
]


class SpamFilter:
    def __init__(self, config):
        self.config = config
        self._recent = {}

    def should_filter(self, message):
        if not self.config.spam_filter_enabled:
            return False
        text = message.texto.strip()
        if len(text) < self.config.min_message_length:
            return True
        if self._is_emoji_only(text):
            return True
        if self._is_repeated(text, message.jugador):
            return True
        if self._is_spam_pattern(text):
            return True
        return False

    def _is_repeated(self, text, player):
        if player not in self._recent:
            self._recent[player] = deque(maxlen=5)
        last = self._recent[player][-1] if self._recent[player] else None
        self._recent[player].append(text)
        return last is not None and text.lower() == last.lower()

    def _is_emoji_only(self, text):
        stripped = _EMOJI_PATTERN.sub("", text)
        return len(stripped.strip()) == 0 and len(text) > 0

    def _is_spam_pattern(self, text):
        for pattern in _SPAM_PATTERNS:
            if pattern.search(text):
                return True
        return False
