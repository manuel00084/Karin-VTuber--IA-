"""Plugins Tab — manage extensions."""
import customtkinter as ctk

from src.ui.theme import (
    BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD,
    AMB_T, BLU_T,
    TXT, TXT_DIM as MUT,
)
from src.ui.widgets import mk, lb


def build_tab_plugins(parent, app):
    self = app
    tab = ctk.CTkScrollableFrame(parent, fg_color=BG, corner_radius=0,
                                  scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD)

    # Tabs/paneles aportados por plugins (retornados por on_ui_tab)
    plugin_frames = self._plugin_manager.emit("ui_tab", parent)
    for pf in plugin_frames:
        if pf and isinstance(pf, ctk.CTkFrame):
            pf.pack(fill="x", padx=14, pady=(6, 0))

    card = mk(tab, accent=True)
    card.pack(fill="x", padx=14, pady=(12, 6))
    lb(card, "🧩  Gestión de Plugins", sz=16, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(card, "Extensiones que agregan funcionalidad a Karin VTuber",
       sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 4))

    def _recargar():
        self._plugin_manager.reload_all()
        self._guardar_config_panel()
        for k in list(self._tabs.keys()):
            if k.startswith("_plugin_"):
                self._tabs[k].destroy()
                del self._tabs[k]
                self._tab_built.discard(k)
        if "plugins" in self._tabs:
            self._tabs["plugins"].destroy()
            del self._tabs["plugins"]
            self._tab_built.discard("plugins")
        self._tab("plugins")

    btn_row = ctk.CTkFrame(card, fg_color="transparent")
    btn_row.pack(fill="x", padx=14, pady=(4, 4))
    ctk.CTkButton(btn_row, text="🔄 Recargar plugins", fg_color=PURP, text_color=TXT,
                  height=28, corner_radius=8, command=_recargar).pack(side="left")

    info = self._plugin_manager.get_plugins_info()

    if not info:
        ctk.CTkFrame(card, height=1, fg_color="#2a2a3e").pack(fill="x", padx=14, pady=(6, 6))
        lb(card, "No hay plugins instalados.", sz=12, col=MUT).pack(padx=14, pady=20)
        lb(card, "Crea una carpeta en plugins/ con un manifest.json",
           sz=10, col=MUT).pack(padx=14, pady=(0, 10))
        ctk.CTkFrame(card, height=6, fg_color="transparent").pack()
        return tab

    for p in info:
        p_card = mk(tab)
        p_card.pack(fill="x", padx=14, pady=(0, 6))

        header = ctk.CTkFrame(p_card, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(10, 2))

        estado = "✅" if p["loaded"] else "⬜"
        lb(header, f"{estado}  {p['name']}", sz=13, bold=True, col=TXT).pack(side="left")
        lb(header, f"v{p['version']}", sz=10, col=MUT).pack(side="left", padx=(8, 0))

        if p["gpu"]:
            lb(header, "⚡ GPU", sz=9, col=AMB_T).pack(side="right", padx=(0, 4))
        if p["ram_mb"]:
            lb(header, f"💾 {p['ram_mb']}MB", sz=9, col=MUT).pack(side="right", padx=(0, 8))

        ctk.CTkFrame(p_card, height=1, fg_color="#2a2a3e").pack(fill="x", padx=14, pady=(6, 4))

        if p["description"]:
            lb(p_card, p["description"], sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 2))
        lb(p_card, f"✍️  {p['author']}", sz=9, col=MUT).pack(anchor="w", padx=14, pady=(0, 2))
        if p.get("hooks"):
            hooks_str = ", ".join(p["hooks"])
            lb(p_card, f"🔌 Hooks: {hooks_str}", sz=9, col=BLU_T).pack(anchor="w", padx=14, pady=(0, 10))

        plugin_switches = [
            (k, v) for k, v in self._plugin_api._switches.items()
            if k.startswith(f"plugin.{p['name'].lower().replace(' ', '_')}.")
        ]
        for full_key, sw_info in plugin_switches:
            sw_row = ctk.CTkFrame(p_card, fg_color="transparent")
            sw_row.pack(fill="x", padx=14, pady=2)
            valor = self._plugin_api.get_switch(full_key)
            sw = ctk.CTkSwitch(sw_row, text=sw_info["label"],
                               font=("Segoe UI", 11),
                               switch_width=36, switch_height=18)
            sw.select() if valor else sw.deselect()
            sw.pack(side="left", padx=(0, 8))
            sw.configure(command=lambda k=full_key, s=sw: self._plugin_api.set_config(k, bool(s.get())))

    return tab
