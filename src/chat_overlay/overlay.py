import tkinter as tk
import threading
import time

from src.bot.twitch_bot import get_twitch_messages, send_chat_message
from src.utils.chat_translator import auto_translate, translate, user_langs

try:
    import vosk
    import sounddevice as sd
    import numpy as np
    _VOSK_OK = True
except ImportError:
    _VOSK_OK = False


class ChatOverlay:
    def __init__(self, opacity=0.88, font_size=12):
        self._window = None
        self._visible = False
        self._opacity = opacity
        self._font_size = font_size
        self._bg = "#1a1a2e"
        self._fg = "#e0e0e0"
        self._accent = "#a855f7"
        self._border_color = "#a855f7"
        self._x = 200
        self._y = 200
        self._drag_data = {"x": 0, "y": 0}
        self._chat_history = []
        self._stt_thread = None
        self._stt_running = False
    
    def _create_window(self):
        if self._window is not None:
            return
        self._window = tk.Toplevel()
        self._window.title("Karin Chat Overlay")
        self._window.geometry(f"420x520+{self._x}+{self._y}")
        self._window.minsize(280, 300)
        self._window.overrideredirect(True)
        self._window.attributes("-topmost", True)
        self._window.attributes("-alpha", self._opacity)
        self._window.configure(bg=self._border_color)

        inner = tk.Frame(self._window, bg=self._bg)
        inner.pack(fill="both", expand=True, padx=2, pady=2)

        header = tk.Frame(inner, bg="#16213e", height=30)
        header.pack(fill="x")
        header.pack_propagate(False)

        title = tk.Label(header, text="🌐  Chat Twitch", bg="#16213e",
                         fg=self._accent, font=("Segoe UI", 10, "bold"))
        title.pack(side="left", padx=10, pady=4)

        close_btn = tk.Label(header, text="✕", bg="#16213e",
                             fg="#e74c3c", font=("Segoe UI", 12, "bold"), cursor="hand2")
        close_btn.pack(side="right", padx=8)
        close_btn.bind("<Button-1>", lambda e: self.hide())

        for w in (header, title, close_btn):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_move)

        self._chat_text = tk.Text(
            inner, bg=self._bg, fg=self._fg,
            font=("Segoe UI", self._font_size),
            wrap="word", state="disabled",
            relief="flat", borderwidth=0,
            padx=8, pady=6,
            highlightthickness=0,
            cursor="arrow",
        )
        self._chat_text.pack(fill="both", expand=True)

        input_frame = tk.Frame(inner, bg=self._bg, height=40)
        input_frame.pack(fill="x", side="bottom")
        input_frame.pack_propagate(False)

        self._entry_var = tk.StringVar()
        self._entry = tk.Entry(
            input_frame, textvariable=self._entry_var,
            bg="#16213e", fg=self._fg,
            font=("Segoe UI", 11),
            relief="flat", borderwidth=0,
            insertbackground=self._accent,
            highlightthickness=1,
            highlightbackground="#2a2a4e",
            highlightcolor=self._accent,
        )
        self._entry.pack(side="left", fill="x", expand=True, padx=(6, 2), pady=4)
        self._entry.bind("<Return>", lambda e: self._on_send())

        mic_btn = tk.Label(input_frame, text="🎤", bg="#16213e",
                           fg=self._accent, font=("Segoe UI", 14), cursor="hand2")
        mic_btn.pack(side="left", padx=2)
        mic_btn.bind("<Button-1>", lambda e: self._toggle_stt())

        send_btn = tk.Label(input_frame, text="➤", bg=self._accent,
                            fg="#ffffff", font=("Segoe UI", 12, "bold"),
                            cursor="hand2", padx=8)
        send_btn.pack(side="right", padx=6, pady=4)
        send_btn.bind("<Button-1>", lambda e: self._on_send())

        if not _VOSK_OK:
            mic_btn.configure(fg="#555")
            mic_btn.configure(text="🎤✖")

        self._apply_win32_styles()
        self._poll_chat()

    def _apply_win32_styles(self):
        if not self._window:
            return
        try:
            import ctypes
            hwnd = self._window.winfo_id()
            user32 = ctypes.windll.user32
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x80000
            WS_EX_TOOLWINDOW = 0x80
            WS_EX_NOACTIVATE = 0x08000000
            current = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(
                hwnd, GWL_EXSTYLE,
                current | WS_EX_LAYERED | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
            )
            user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0002 | 0x0001)
        except Exception:
            pass

    def _drag_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _drag_move(self, event):
        x = self._window.winfo_x() + event.x - self._drag_data["x"]
        y = self._window.winfo_y() + event.y - self._drag_data["y"]
        self._window.geometry(f"+{x}+{y}")

    def show(self):
        if not self._window:
            self._create_window()
        self._visible = True
        self._window.deiconify()
        self._entry.focus()

    def hide(self):
        self._visible = False
        if self._window:
            self._window.withdraw()
        self._stop_stt()

    def toggle(self):
        if self._visible:
            self.hide()
        else:
            self.show()

    def destroy(self):
        self._stop_stt()
        if self._window:
            self._window.destroy()
            self._window = None
        self._visible = False

    def _append_chat(self, text, tag=None):
        try:
            self._chat_text.configure(state="normal")
            self._chat_text.insert("end", text + "\n", tag or ())
            self._chat_text.see("end")
            self._chat_text.configure(state="disabled")
        except Exception:
            pass

    def _poll_chat(self):
        if not self._window or not self._visible:
            return
        try:
            msgs = get_twitch_messages(1)
            fresh = []
            for m in msgs:
                if m not in self._chat_history:
                    fresh.append(m)
                    self._chat_history.append(m)
            if len(self._chat_history) > 500:
                self._chat_history = self._chat_history[-300:]
            for f in fresh:
                self._append_chat(f)
        except Exception:
            pass
        try:
            self._window.after(1000, self._poll_chat)
        except Exception:
            pass

    def _on_send(self):
        text = self._entry_var.get().strip()
        if not text:
            return
        self._entry_var.set("")

        self._append_chat(f"→ {text}")
        sent = send_chat_message(text)
        if sent:
            self._append_chat(f"✓  Enviado")
        else:
            self._append_chat(f"✗  Bot no conectado")

    def _toggle_stt(self):
        if not _VOSK_OK:
            self._append_chat("⚠  Instalá vosk + sounddevice: pip install vosk sounddevice")
            return
        if self._stt_running:
            self._stop_stt()
        else:
            self._start_stt()

    def _start_stt(self):
        if self._stt_running or not _VOSK_OK:
            return
        self._stt_running = True
        self._stt_thread = threading.Thread(target=self._stt_loop, daemon=True)
        self._stt_thread.start()
        self._append_chat("🎤  Micrófono activado...")

    def _stop_stt(self):
        self._stt_running = False
        if self._stt_thread:
            self._stt_thread = None

    def _stt_loop(self):
        try:
            from src import PROJECT_ROOT
            import os
            model_path = os.path.join(PROJECT_ROOT, "vosk-model-small-es-0.42")
            if not os.path.isdir(model_path):
                self._safe_append("⚠  Modelo Vosk no encontrado")
                self._stt_running = False
                return
            model = vosk.Model(model_path)
            recognizer = vosk.KaldiRecognizer(model, 16000)
            with sd.RawInputStream(samplerate=16000, blocksize=8000,
                                    dtype="int16", channels=1) as stream:
                while self._stt_running:
                    data, _ = stream.read(4000)
                    if recognizer.AcceptWaveform(data):
                        result = recognizer.Result()
                        import json
                        js = json.loads(result)
                        text = js.get("text", "").strip()
                        if text:
                            self._safe_stt_result(text)
        except Exception as e:
            self._safe_append(f"⚠  Error STT: {e}")
            self._stt_running = False

    def _safe_append(self, text):
        if self._window:
            try:
                self._window.after(0, self._append_chat, text)
            except Exception:
                pass

    def _safe_stt_result(self, text):
        if not self._window:
            return
        try:
            self._window.after(0, self._handle_stt_text, text)
        except Exception:
            pass

    def _handle_stt_text(self, text):
        self._append_chat(f"🎤  {text}")
        self._entry_var.set(text)
        self._on_send()
