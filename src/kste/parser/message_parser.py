import re
import time
from enum import Enum
from dataclasses import dataclass, field


class ChatChannel(Enum):
    GENERAL = "general"
    PARTY = "party"
    GUILD = "guild"
    WHISPER = "whisper"
    TRADE = "trade"
    SYSTEM = "system"
    WORLD = "world"
    UNKNOWN = "unknown"


@dataclass
class ChatMessage:
    jugador: str
    texto: str
    canal: ChatChannel = ChatChannel.GENERAL
    idioma: str = "unknown"
    timestamp: float = 0.0
    traduccion: str = ""
    es_traduccion: bool = False
    protegido: list = field(default_factory=list)


_CHANNEL_PREFIXES = [
    (ChatChannel.WHISPER, re.compile(
        r'^(.+?)\s*(?:>|→|->)\s*(.+?)\s*:\s*(.+)$'
    )),
    (ChatChannel.PARTY, re.compile(
        r'^\[Party\]\s*(.+?)\s*:\s*(.+)$', re.IGNORECASE
    )),
    (ChatChannel.GUILD, re.compile(
        r'^\[Guild\]\s*(.+?)\s*:\s*(.+)$', re.IGNORECASE
    )),
    (ChatChannel.TRADE, re.compile(
        r'^\[Trade\]\s*(.+?)\s*:\s*(.+)$', re.IGNORECASE
    )),
    (ChatChannel.WORLD, re.compile(
        r'^\[World\]\s*(.+?)\s*:\s*(.+)$', re.IGNORECASE
    )),
    (ChatChannel.SYSTEM, re.compile(
        r'^\*{2,}\s*(.+?)\s*\*{2,}$'
    )),
]

_GENERAL_PATTERN = re.compile(r'^(.+?)\s*:\s*(.+)$')


class MessageParser:
    def parse(self, ocr_results, default_channel=ChatChannel.GENERAL):
        messages = []
        for r in ocr_results:
            text = self._clean_text(r.texto)
            if not text or len(text) < 2:
                continue
            channel, player, msg_text = self._detect_channel(text)
            if not msg_text:
                continue
            messages.append(ChatMessage(
                jugador=player,
                texto=msg_text,
                canal=channel,
                timestamp=time.time()
            ))
        return self._merge_consecutive(messages)

    def _detect_channel(self, text):
        for channel, pattern in _CHANNEL_PREFIXES:
            m = pattern.match(text)
            if m:
                groups = m.groups()
                if channel == ChatChannel.SYSTEM:
                    return channel, "Sistema", groups[0]
                if channel == ChatChannel.WHISPER:
                    return channel, groups[0], groups[-1]
                return channel, groups[0], groups[-1]
        m = _GENERAL_PATTERN.match(text)
        if m:
            return ChatChannel.GENERAL, m.group(1).strip(), m.group(2).strip()
        return ChatChannel.UNKNOWN, "Desconocido", text

    def _clean_text(self, text):
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        text = text.replace('|', 'I').replace('0o', 'oo')
        return text

    def _merge_consecutive(self, messages):
        if not messages:
            return []
        merged = [messages[0]]
        for msg in messages[1:]:
            prev = merged[-1]
            if (msg.jugador == prev.jugador and
                    msg.canal == prev.canal and
                    msg.timestamp - prev.timestamp < 3.0):
                prev.texto += " " + msg.texto
            else:
                merged.append(msg)
        return merged
