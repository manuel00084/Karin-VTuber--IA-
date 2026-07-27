import tkinter as tk
import threading
from collections import deque
from src.utils.log import info, warn
from src.kste.config.kste_config import KSTEConfig


class KSTEOverlay:
    def __init__(self, config):
        self.config = config
        self._root = None
        self._canvas = None
        self._messages = deque(maxlen=30)
        self._visible = False
        self._on_reply_callback = None
        self._lock = threading.Lock()

    def set_on_reply_callback(self, callback):
        self._on_reply_callback = callback

    def show(self):
        if self._visible:
            return
        try:
            self._root = tk.Toplevel()
            self._root.title("KSTE Overlay")
            self._root.geometry("420x500")
            self._root.attributes("-topmost", True)
            self._root.overrideredirect(True)
            self._root.attributes("-alpha", self.config.overlay_opacity)
            self._root.configure(bg=self.config.overlay_bg_color)
            self._canvas = tk.Canvas(
                self._root,
                bg=self.config.overlay_bg_color,
                highlightthickness=0
            )
            self._canvas.pack(fill="both", expand=True)
            self._apply_win32_styles()
            self._canvas.bind("<ButtonPress-1>", self._drag_start)
            self._canvas.bind("<B1-Motion>", self._drag_move)
            self._render_messages()
            self._visible = True
            info("KSTE overlay shown")
        except Exception as e:
            warn(f"KSTE overlay show error: {e}")

    def hide(self):
        if self._root:
            try:
                self._root.withdraw()
            except Exception:
                pass
        self._visible = False

    def toggle(self):
        if self._visible:
            self.hide()
        else:
            self.show()

    def destroy(self):
        if self._root:
            try:
                self._root.destroy()
            except Exception:
                pass
            self._root = None
        self._visible = False

    def add_message(self, player, original, translated, lang, channel="general"):
        with self._lock:
            self._messages.append({
                "player": player,
                "original": original,
                "translated": translated,
                "lang": lang,
                "channel": channel,
            })
        if self._root and self._visible:
            try:
                self._root.after(0, self._render_messages)
            except Exception:
                pass

    def clear(self):
        with self._lock:
            self._messages.clear()
        if self._root and self._visible:
            try:
                self._root.after(0, self._render_messages)
            except Exception:
                pass

    def _render_messages(self):
        if not self._canvas:
            return
        self._canvas.delete("all")
        with self._lock:
            msgs = list(self._messages)
        y = 10
        for i, msg in enumerate(msgs):
            lang_tag = f"[{msg['lang'].upper()}]" if msg['lang'] != "unknown" else ""
            player_text = f"{lang_tag} {msg['player']}"
            self._canvas.create_text(
                10, y, anchor="w",
                text=player_text,
                fill=self.config.overlay_border_color,
                font=("Consolas", self.config.overlay_font_size - 1, "bold")
            )
            y += 18
            orig_text = msg['original']
            if len(orig_text) > 80:
                orig_text = orig_text[:77] + "..."
            self._canvas.create_text(
                10, y, anchor="w",
                text=orig_text,
                fill="#aaaaaa",
                font=("Consolas", self.config.overlay_font_size - 2)
            )
            y += 16
            trans_text = msg['translated']
            if len(trans_text) > 80:
                trans_text = trans_text[:77] + "..."
            self._canvas.create_text(
                10, y, anchor="w",
                text=trans_text,
                fill=self.config.overlay_text_color,
                font=("Consolas", self.config.overlay_font_size - 1)
            )
            y += 20
            btn_id = self._canvas.create_text(
                400, y - 10, anchor="e",
                text="[Responder]",
                fill="#a855f7",
                font=("Consolas", 9),
                tags=f"reply_{i}"
            )
            self._canvas.tag_bind(btn_id, "<Button-1>",
                                  lambda e, p=msg['player']: self._on_reply_click(p))
            y += 10
            self._canvas.create_line(10, y, 410, y, fill="#333333")
            y += 5
        if y > 490:
            self._root.geometry(f"420x{min(y + 20, 700)}")

    def _on_reply_click(self, player):
        if self._on_reply_callback:
            try:
                self._on_reply_callback(player)
            except Exception as e:
                warn(f"KSTE reply callback error: {e}")

    def _apply_win32_styles(self):
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self._root.winfo_id())
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_NOACTIVATE = 0x08000000
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        except Exception:
            pass

    def _drag_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _drag_move(self, event):
        dx = event.x - self._drag_x
        dy = event.y - self._drag_y
        x = self._root.winfo_x() + dx
        y = self._root.winfo_y() + dy
        self._root.geometry(f"+{x}+{y}")
