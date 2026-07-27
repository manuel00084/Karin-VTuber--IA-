import tkinter as tk
import threading, time, math, os, random
from src import PROJECT_ROOT


class AlertOverlay:
    STYLES = {
        "follow": {
            "icon": "⭐", "accent": "#c084fc", "bg1": "#1a0a2e", "bg2": "#2d1b4e",
            "sound": "follow.wav", "title": "Nuevo Follow", "h": 160,
        },
        "sub": {
            "icon": "🌟", "accent": "#f59e0b", "bg1": "#2e1a00", "bg2": "#4e3000",
            "sound": "sub.wav", "title": "Nuevo Suscriptor", "h": 200,
        },
        "resub": {
            "icon": "🔥", "accent": "#f97316", "bg1": "#2e1a00", "bg2": "#4e3000",
            "sound": "sub.wav", "title": "Meses Suscrito", "h": 200,
        },
        "bit": {
            "icon": "💎", "accent": "#3b82f6", "bg1": "#001a2e", "bg2": "#003d6b",
            "sound": "bit.wav", "title": "Bits", "h": 180,
        },
        "raid": {
            "icon": "⚔️", "accent": "#ef4444", "bg1": "#2e0000", "bg2": "#5c0000",
            "sound": "raid.wav", "title": "Raid Incoming", "h": 200,
        },
        "donation": {
            "icon": "❤️", "accent": "#ec4899", "bg1": "#2e0018", "bg2": "#5c0030",
            "sound": "donation.wav", "title": "Donación", "h": 180,
        },
    }

    def __init__(self):
        self._window = None
        self._canvas = None
        self._visible = False
        self._queue = []
        self._processing = False
        self._x = 100
        self._y = 80
        self._opacity = 0.92
        self._duration = 6
        self._sound_enabled = True
        self._alerts_dir = os.path.join(PROJECT_ROOT, "assets", "alerts")
        self._w = 480
        self._sound_paths = {}  # event_type -> custom path override

    def _create_window(self):
        if self._window is not None:
            return
        import ctypes
        user32 = ctypes.windll.user32
        sw = user32.GetSystemMetrics(0)

        self._window = tk.Toplevel()
        self._window.title("Karin Alertas")
        self._window.geometry(f"{self._w}x200+{(sw - self._w)//2}+{self._y}")
        self._window.overrideredirect(True)
        self._window.attributes("-topmost", True)
        self._window.attributes("-alpha", self._opacity)
        self._window.configure(bg="#000000")

        self._canvas = tk.Canvas(
            self._window, width=self._w, height=200,
            bg="#000000", highlightthickness=0,
        )
        self._canvas.pack(fill="both", expand=True)
        self._canvas.bind("<ButtonPress-1>", self._drag_start)
        self._canvas.bind("<B1-Motion>", self._drag_move)
        self._canvas.bind("<Double-Button-1>", self._drag_center)
        self._window.protocol("WM_DELETE_WINDOW", self.hide)
        self._apply_win32_styles()

    def _apply_win32_styles(self):
        if not self._window:
            return
        try:
            import ctypes
            hwnd = self._window.winfo_id()
            user32 = ctypes.windll.user32
            user32.SetWindowLongW(hwnd, -20,
                user32.GetWindowLongW(hwnd, -20) | 0x80000 | 0x20 | 0x80 | 0x08000000)
            user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0002 | 0x0001)
        except Exception:
            pass

    _drag_data = {"x": 0, "y": 0, "dragging": False}

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
        try:
            import ctypes
            user32 = ctypes.windll.user32
            sw = user32.GetSystemMetrics(0)
        except Exception:
            sw = 1920
        self._x = (sw - self._w) // 2
        self._y = 80
        if self._window:
            self._window.geometry(f"{self._w}x200+{self._x}+{self._y}")

    # ── Public API ──

    def show(self):
        self._create_window()
        if self._window:
            self._visible = True
            self._window.after(0, self._do_show)

    def _do_show(self):
        if self._window:
            try:
                self._window.deiconify()
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

    def destroy(self):
        self._visible = False
        if self._window:
            self._window.after(0, self._do_destroy)

    def _do_destroy(self):
        if self._window:
            try:
                self._window.destroy()
            except Exception:
                pass
            self._window = None
            self._canvas = None

    @property
    def is_visible(self):
        return self._visible

    # ── Sound ──

    def _play_sound(self, event_type):
        if not self._sound_enabled:
            return
        sound_path = self._sound_paths.get(event_type)
        if not sound_path or not os.path.exists(sound_path):
            style = self.STYLES.get(event_type)
            if not style:
                return
            sound_path = os.path.join(self._alerts_dir, style["sound"])
        if os.path.exists(sound_path):
            try:
                import winsound
                winsound.PlaySound(sound_path, winsound.SND_ASYNC)
            except Exception:
                pass
        else:
            try:
                import winsound
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
            except Exception:
                pass

    # ── Alert Queue ──

    def queue_alert(self, event_type, username, message="", months=0, bits=0, viewers=0):
        self._queue.append({
            "type": event_type,
            "username": username,
            "message": message,
            "months": months,
            "bits": bits,
            "viewers": viewers,
        })
        if self._window and self._visible:
            self._window.after(0, self._process_queue)

    def _process_queue(self):
        if self._processing or not self._queue or not self._window:
            return
        self._processing = True
        self._show_alert(self._queue.pop(0))

    # ── Rendering ──

    def _show_alert(self, alert):
        if not self._canvas:
            self._processing = False
            return
        c = self._canvas
        style = self.STYLES.get(alert["type"], self.STYLES["follow"])
        w = self._w
        h = style["h"]
        self._window.geometry(f"{w}x{h}")
        c.configure(width=w, height=h)
        c.delete("all")

        self._play_sound(alert["type"])

        bg1, bg2 = style["bg1"], style["bg2"]
        accent = style["accent"]
        icon = style["icon"]
        username = alert["username"]

        for i in range(h):
            r = i / h
            cr = self._lerp_color(bg1, bg2, r)
            c.create_line(0, i, w, i, fill=cr)

        c.create_rectangle(2, 2, w - 2, h - 2, outline=accent, width=2)

        cx = w // 2
        icon_size = 40 if h >= 180 else 32
        c.create_text(cx, h * 0.25, text=icon, font=("Segoe UI", icon_size), anchor="center")

        title_y = h * 0.48
        title = style["title"]
        if alert["type"] == "resub":
            title = f"{alert['months']} {style['title']}"
        c.create_text(cx, title_y, text=title, fill=accent,
                      font=("Segoe UI", 16, "bold"), anchor="center")

        c.create_text(cx, h * 0.68, text=username, fill="#ffffff",
                      font=("Segoe UI", 20, "bold"), anchor="center")

        if alert["type"] == "bit":
            c.create_text(cx, h * 0.86, text=f"{alert['bits']} bits", fill=style["accent"],
                          font=("Segoe UI", 13, "bold"), anchor="center")
        elif alert["type"] == "raid":
            c.create_text(cx, h * 0.86, text=f"{alert['viewers']} espectadores", fill="#fca5a5",
                          font=("Segoe UI", 13), anchor="center")
        elif alert["message"]:
            msg = alert["message"] if len(alert["message"]) < 50 else alert["message"][:47] + "..."
            c.create_text(cx, h * 0.86, text=f'"{msg}"', fill="#d1d5db",
                          font=("Segoe UI", 11, "italic"), anchor="center")

        self._animate_in(c, w, h, lambda: self._schedule_dismiss(c, w, h))

    @staticmethod
    def _lerp_color(c1, c2, t):
        def _h(hx):
            return int(hx[1:3], 16), int(hx[3:5], 16), int(hx[5:7], 16)
        r1, g1, b1 = _h(c1)
        r2, g2, b2 = _h(c2)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return f"#{r:02x}{g:02x}{b:02x}"

    # ── Animations with easing ──

    def _animate_in(self, c, w, h, done_cb):
        steps = 12
        def _ease_out(t):
            return 1 - (1 - t) ** 3
        def _step(i):
            if not c.winfo_exists():
                return
            progress = i / steps
            eased = _ease_out(progress)
            offset_y = int(40 * (1 - eased))
            alpha = eased
            try:
                self._window.attributes("-alpha", self._opacity * alpha)
                self._window.geometry(f"+{self._x}+{self._y + offset_y}")
            except Exception:
                pass
            if i < steps:
                c.after(25, lambda: _step(i + 1))
            else:
                done_cb()
        _step(0)

    def _animate_out(self, c, w, h, done_cb):
        steps = 10
        def _ease_in(t):
            return t ** 3
        def _step(i):
            if not c.winfo_exists():
                return
            progress = i / steps
            eased = _ease_in(progress)
            alpha = 1 - eased
            offset_y = int(30 * eased)
            try:
                self._window.attributes("-alpha", self._opacity * alpha)
                self._window.geometry(f"+{self._x}+{self._y + offset_y}")
            except Exception:
                pass
            if i < steps:
                c.after(25, lambda: _step(i + 1))
            else:
                done_cb()
        _step(0)

    def _schedule_dismiss(self, c, w, h):
        c.after(self._duration * 1000, lambda: self._animate_out(c, w, h, self._on_alert_done))

    def _on_alert_done(self):
        self._processing = False
        if self._queue:
            self._show_alert(self._queue.pop(0))
        else:
            if self._window:
                try:
                    self._window.attributes("-alpha", self._opacity)
                except Exception:
                    pass

    def set_position(self, x, y):
        self._x, self._y = x, y
        if self._window:
            self._window.after(0, lambda: self._window.geometry(f"+{x}+{y}"))

    def set_opacity(self, op):
        self._opacity = max(0.1, min(1.0, op))
        if self._window:
            self._window.after(0, lambda: self._window.attributes("-alpha", self._opacity))

    def set_duration(self, sec):
        self._duration = max(2, min(30, sec))

    def set_sound_enabled(self, enabled):
        self._sound_enabled = enabled

    def set_sound_path(self, event_type, path):
        if path:
            self._sound_paths[event_type] = path
        else:
            self._sound_paths.pop(event_type, None)

    def set_sound_paths(self, paths):
        self._sound_paths = {k: v for k, v in paths.items() if v}
