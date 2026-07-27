"""Karin VTuber — Reusable Glassmorphism UI Widgets."""
import customtkinter as ctk
from src.ui.theme import *


class ToolTip:
    """Tooltip hover — aparece al pasar el mouse, se oculta al salir."""

    def __init__(self, widget, text, delay=400):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._tip_window = None
        self._after_id = None
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, event=None):
        self._cancel()
        self._after_id = self.widget.after(self.delay, self._show)

    def _on_leave(self, event=None):
        self._cancel()
        self._hide()

    def _cancel(self):
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self):
        if self._tip_window:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.configure(fg_color="#1e1e2e")
        lbl = ctk.CTkLabel(tw, text=self.text, font=("Segoe UI", 11),
                           text_color="#e2e8f0", padx=10, pady=6,
                           wraplength=320, justify="left")
        lbl.pack()
        self._tip_window = tw

    def _hide(self):
        if self._tip_window:
            self._tip_window.destroy()
            self._tip_window = None


def mk(parent, accent=False, **kwargs):
    """Create a glass card container. Silently ignores unsupported kwargs."""
    defaults = {"fg_color": CARD_BG_HEX, "corner_radius": CORNER, "border_width": 1, "border_color": CARD_BORDER}
    allowed = {'fg_color', 'corner_radius', 'border_width', 'border_color', 'width', 'height'}
    filtered = {k: v for k, v in kwargs.items() if k in allowed}
    defaults.update(filtered)
    f = ctk.CTkFrame(parent, **defaults)
    if accent:
        bar = ctk.CTkFrame(f, fg_color=CARD_BORDER, height=3, corner_radius=0)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)
    return f


def mk_row(parent, **kwargs):
    """Create a horizontal row inside a card."""
    defaults = {"fg_color": "transparent"}
    defaults.update(kwargs)
    return ctk.CTkFrame(parent, **defaults)


def lb(parent, text, sz=12, bold=False, col=TXT, **kwargs):
    """Create a label."""
    weight = "bold" if bold else "normal"
    return ctk.CTkLabel(parent, text=text, font=("Segoe UI", sz, weight),
                        text_color=col, **kwargs)


def btn(parent, text, command=None, color=PURP, hover=None, sz=12, height=28, **kwargs):
    """Create a styled button."""
    if hover is None:
        hover = {"primary": PURP_DARK, "danger": "#b91c1c", "secondary": "#4b5563", "success": "#16a34a"}.get(color, PURP_DARK)
        if color == PURP:
            hover = PURP_DARK
        elif color == RED_T:
            hover = "#b91c1c"
        elif color == GREEN:
            hover = "#16a34a"
        else:
            hover = "#4b5563"
    return ctk.CTkButton(parent, text=text, command=command,
                        fg_color=color, hover_color=hover,
                        corner_radius=CORNER_SM, font=(FONT[0], sz),
                        height=height, **kwargs)


def bt(parent, text, bg, fg, command, height=36, **kwargs):
    """Create a styled button with auto-lightened hover (compat with main.py)."""
    import colorsys
    def _lighten(hex_color, factor=0.15):
        try:
            r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
            h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
            l = min(1, l + factor * 0.3)
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        except Exception:
            return bg
    return ctk.CTkButton(parent, text=text, fg_color=bg, text_color=fg,
                         hover_color=_lighten(bg),
                         font=("Segoe UI", 12, "bold"), corner_radius=10,
                         height=height, command=command, **kwargs)


def entry(parent, variable=None, placeholder="", **kwargs):
    """Create a styled entry field."""
    defaults = {"fg_color": "#1e1e2e", "border_color": CARD_BORDER, "text_color": TXT,
                "font": FONT_MONO, "corner_radius": CORNER_SM, "placeholder_text": placeholder}
    defaults.update(kwargs)
    if variable:
        defaults["textvariable"] = variable
    return ctk.CTkEntry(parent, **defaults)


def switch(parent, text, variable, color=GREEN, **kwargs):
    """Create a toggle switch."""
    return ctk.CTkSwitch(parent, text=text, variable=variable,
                        font=FONT_SMALL, fg_color="#374151",
                        progress_color=color, button_color=color, **kwargs)


def slider(parent, variable, from_=0, to=1, **kwargs):
    """Create a styled slider."""
    defaults = {"fg_color": "#374151", "progress_color": PURP, "button_color": PURP, "button_hover_color": PURP_LIGHT}
    defaults.update(kwargs)
    return ctk.CTkSlider(parent, from_=from_, to=to, variable=variable, **defaults)


def cb(parent, values, **kwargs):
    """Create a styled combobox."""
    kwargs.setdefault("fg_color", CARD_BG_HEX)
    kwargs.setdefault("border_color", BORD)
    kwargs.setdefault("button_color", PURP)
    kwargs.setdefault("dropdown_fg_color", CARD2)
    kwargs.setdefault("dropdown_hover_color", "#2a2a42")
    kwargs.setdefault("font", ("Segoe UI", 11))
    return ctk.CTkComboBox(parent, values=values, **kwargs)


def option_menu(parent, variable, values, **kwargs):
    """Create a styled option menu."""
    defaults = {"fg_color": "#1e1e2e", "button_color": PURP, "font": FONT_SMALL}
    defaults.update(kwargs)
    return ctk.CTkOptionMenu(parent, variable=variable, values=values, **defaults)


def separator(parent):
    """Create a subtle separator line."""
    sep = ctk.CTkFrame(parent, height=1, fg_color=CARD_BORDER, corner_radius=0)
    return sep


class GlassButton(ctk.CTkButton):
    """Button with glassmorphism hover glow effect."""
    def __init__(self, parent, text="", command=None, color=PURP, glow=None, **kwargs):
        self._base_color = color
        self._glow_color = glow or self._lighten(color, 0.3)
        self._default_color = color
        super().__init__(parent, text=text, command=command,
                        fg_color=color, hover_color=self._glow_color,
                        corner_radius=CORNER_SM, font=FONT,
                        border_width=0, **kwargs)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        self.configure(border_width=2, border_color=self._glow_color)

    def _on_leave(self, e):
        self.configure(border_width=0)

    @staticmethod
    def _lighten(hex_color, factor):
        """Lighten a hex color for glow effect."""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return f'#{r:02x}{g:02x}{b:02x}'
