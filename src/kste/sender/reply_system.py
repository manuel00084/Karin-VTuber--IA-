import subprocess
import time
from src.utils.log import info, warn


class ReplySystem:
    def __init__(self, translator, config):
        self.translator = translator
        self.config = config

    def send_reply(self, text_es, target_player, player_profiles=None):
        if not text_es or not text_es.strip():
            return False
        target_lang = "en"
        if player_profiles:
            profile = player_profiles.get(target_player)
            if profile and profile.idioma_detectado != "unknown":
                target_lang = profile.idioma_detectado
        try:
            translated = self.translator.translate(
                text_es, source="es", target=target_lang
            )
            if not translated:
                warn("KSTE reply: translation returned empty")
                return False
        except Exception as e:
            warn(f"KSTE reply translate error: {e}")
            return False
        if not self._to_clipboard(translated):
            return False
        if self.config.auto_paste:
            self._paste_and_send()
        info(f"KSTE reply sent: {text_es} -> {translated} [{target_lang}]")
        return True

    def _to_clipboard(self, text):
        try:
            import ctypes
            CF_UNICODETEXT = 13
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            user32.OpenClipboard(0)
            user32.EmptyClipboard()
            data = text.encode("utf-16-le") + b"\x00\x00"
            h_mem = kernel32.GlobalAlloc(0x0042, len(data))
            p_mem = kernel32.GlobalLock(h_mem)
            ctypes.memmove(p_mem, data, len(data))
            kernel32.GlobalUnlock(h_mem)
            user32.SetClipboardData(CF_UNICODETEXT, h_mem)
            user32.CloseClipboard()
            return True
        except Exception:
            try:
                import pyperclip
                pyperclip.copy(text)
                return True
            except Exception as e:
                warn(f"KSTE clipboard error: {e}")
                return False

    def _paste_and_send(self):
        try:
            import ctypes
            time.sleep(0.05)
            KEYEVENTF_KEYUP = 0x0002
            VK_CONTROL = 0x11
            VK_V = 0x56
            VK_RETURN = 0x0D
            user32 = ctypes.windll.user32
            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            user32.keybd_event(VK_V, 0, 0, 0)
            user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
            if self.config.auto_send_enter:
                time.sleep(0.05)
                user32.keybd_event(VK_RETURN, 0, 0, 0)
                user32.keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP, 0)
        except Exception as e:
            warn(f"KSTE paste error: {e}")
