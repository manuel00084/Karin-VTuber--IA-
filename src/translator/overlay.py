"""
overlay.py — Ventana flotante para mostrar traducciones sobre el juego.
Usa Win32 API directamente para forzar TOPMOST y click-through.
Thread-safe: todas las actualizaciones via after() al hilo principal.
Soporta arrastrar con el mouse (click sostenido) y doble clic para centrar.
"""

import tkinter as tk
import threading


class TranslationOverlay:
    def __init__(self):
        self._window = None
        self._label = None
        self._visible = False
        self._text = ""
        self._color = "#00ff00"
        self._bg_color = "#000000"
        self._border_color = "#a855f7"
        self._opacity = 0.85
        self._font_size = 16
        self._x = 100
        self._y = 100
        self._drag_data = {"x": 0, "y": 0, "dragging": False}

    def _create_window(self):
        if self._window is not None:
            return
        self._window = tk.Toplevel()
        self._window.title("Karin Traductor")
        self._window.geometry(f"600x200+{self._x}+{self._y}")
        self._window.minsize(200, 50)
        self._window.overrideredirect(True)
        self._window.attributes("-topmost", True)
        self._window.attributes("-alpha", self._opacity)
        self._window.configure(bg=self._border_color)

        # Inner frame (borde visible de 2px color morado)
        inner = tk.Frame(self._window, bg=self._bg_color)
        inner.pack(fill="both", expand=True, padx=2, pady=2)

        self._label = tk.Label(
            inner,
            text=self._text or "Esperando traducción...",
            fg=self._color,
            bg=self._bg_color,
            font=("Segoe UI", self._font_size),
            wraplength=560,
            justify="left",
            padx=10,
            pady=10,
        )
        self._label.pack(fill="both", expand=True)

        # Aplicar texto pendiente (si se llamó update_text antes de crear la ventana)
        if self._text:
            self._label.configure(text=self._text)

        # Drag support: click en cualquier parte de la ventana arrastra
        for widget in (self._window, inner, self._label):
            widget.bind("<ButtonPress-1>", self._drag_start)
            widget.bind("<B1-Motion>", self._drag_move)
            widget.bind("<Double-Button-1>", self._drag_center)

        self._window.protocol("WM_DELETE_WINDOW", self.hide)

        self._apply_win32_styles()

    # ── Win32 API ──────────────────────────────────────────

    def _apply_win32_styles(self):
        if not self._window:
            return
        try:
            import ctypes
            hwnd = self._window.winfo_id()
            user32 = ctypes.windll.user32

            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x80000
            WS_EX_TRANSPARENT = 0x20
            WS_EX_TOOLWINDOW = 0x80
            WS_EX_NOACTIVATE = 0x08000000

            current = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(
                hwnd, GWL_EXSTYLE,
                current | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
            )

            user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0002 | 0x0001)
        except Exception:
            pass

    def _lift_win32(self):
        if not self._window:
            return
        try:
            import ctypes
            hwnd = self._window.winfo_id()
            ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0002 | 0x0001)
        except Exception:
            pass

    # ── Drag ───────────────────────────────────────────────

    def _drag_start(self, event):
        self._drag_data["x"] = event.x_root
        self._drag_data["y"] = event.y_root
        self._drag_data["dragging"] = True

    def _drag_move(self, event):
        if not self._drag_data["dragging"] or not self._window:
            return
        dx = event.x_root - self._drag_data["x"]
        dy = event.y_root - self._drag_data["y"]
        self._x += dx
        self._y += dy
        self._drag_data["x"] = event.x_root
        self._drag_data["y"] = event.y_root
        self._window.geometry(f"+{self._x}+{self._y}")

    def _drag_center(self, event=None):
        """Doble clic centra la ventana en la pantalla."""
        try:
            import ctypes
            user32 = ctypes.windll.user32
            sw = user32.GetSystemMetrics(0)
            sh = user32.GetSystemMetrics(1)
        except Exception:
            sw, sh = 1920, 1080
        self._x = (sw - 600) // 2
        self._y = (sh - 200) // 2
        if self._window:
            self._window.geometry(f"600x200+{self._x}+{self._y}")

    # ── Public API (thread-safe via after) ─────────────────

    def show(self):
        self._create_window()
        if self._window:
            self._visible = True
            self._window.after(0, self._do_show)

    def _do_show(self):
        if not self._window:
            return
        try:
            self._window.deiconify()
            self._lift_win32()
        except Exception:
            pass

    def hide(self):
        self._visible = False
        if self._window:
            self._window.after(0, self._do_hide)

    def _do_hide(self):
        if self._window:
            try:
                self._window.withdraw()
            except Exception:
                pass

    def update_text(self, text):
        """Thread-safe: actualiza texto y trae al frente.
        Si la ventana aún no existe, guarda el texto para aplicarlo al crearse.
        """
        self._text = text
        if self._window:
            try:
                self._window.after(0, self._do_update_text, text)
                self._window.after(0, self._do_lift)
            except Exception:
                pass  # window destroyed between check and call

    def _do_update_text(self, text):
        if self._label:
            try:
                self._label.configure(text=text)
            except Exception:
                pass

    def _do_lift(self):
        if not self._window or not self._visible:
            return
        try:
            self._window.lift()
            self._window.attributes("-topmost", True)
            self._lift_win32()
        except Exception:
            pass

    def set_position(self, x, y):
        self._x, self._y = x, y
        if self._window:
            self._window.after(0, self._do_set_position, x, y)

    def _do_set_position(self, x, y):
        if self._window:
            try:
                self._window.geometry(f"+{x}+{y}")
            except Exception:
                pass

    def set_opacity(self, opacity):
        self._opacity = max(0.1, min(1.0, opacity))
        if self._window:
            self._window.after(0, self._do_set_opacity, self._opacity)

    def _do_set_opacity(self, opacity):
        if self._window:
            try:
                self._window.attributes("-alpha", opacity)
            except Exception:
                pass

    def set_font_size(self, size):
        self._font_size = max(10, min(48, size))
        if self._label:
            self._label.after(0, self._do_set_font_size, self._font_size)

    def _do_set_font_size(self, size):
        if self._label:
            try:
                self._label.configure(font=("Segoe UI", size))
            except Exception:
                pass

    def set_colors(self, text_color="#00ff00", bg_color="#000000"):
        self._color = text_color
        self._bg_color = bg_color
        if self._window:
            self._window.after(0, self._do_set_colors, text_color, bg_color)

    def _do_set_colors(self, text_color, bg_color):
        try:
            if self._label:
                self._label.configure(fg=text_color, bg=bg_color)
            if self._window:
                self._window.configure(bg=self._border_color)
        except Exception:
            pass

    def destroy(self):
        self._visible = False
        if self._window:
            try:
                self._window.after(0, self._do_destroy)
            except Exception:
                pass

    def _do_destroy(self):
        if self._window:
            try:
                self._window.destroy()
            except Exception:
                pass
            self._window = None
            self._label = None

    @property
    def is_visible(self):
        return self._visible
