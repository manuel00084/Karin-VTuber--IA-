"""OBS Tab — control OBS Studio from Karin VTuber."""
import customtkinter as ctk

from src.ui.theme import (
    BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD,
    GRN, GRN_T,
    TXT, TXT_DIM as MUT,
)
from src.ui.widgets import mk, lb, ToolTip


def build_tab_obs(parent, app):
    self = app
    tab = ctk.CTkScrollableFrame(parent, fg_color=BG, corner_radius=0,
                                  scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD)

    if self.obs_controller is None:
        from src.obs_controller import OBSController
        self.obs_controller = OBSController(log_fn=self.log)
        from src.core.config import load_config as _lc
        cfg = _lc()
        self.obs_controller.config(
            cfg.get("OBS_HOST", "localhost"),
            int(cfg.get("OBS_PORT", 4455)),
            cfg.get("OBS_PASSWORD", ""),
        )

    c = mk(tab, accent=True)
    c.pack(fill="x", padx=14, pady=(12, 6))
    lb(c, "📺  OBS Studio", sz=16, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(c, "Controla OBS desde Karin VTuber", sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 4))

    obs = self.obs_controller

    estado = mk(tab)
    estado.pack(fill="x", padx=14, pady=(0, 8))
    status_lb = lb(estado, "", sz=11, col=TXT)
    status_lb.pack(anchor="w", padx=14, pady=8)

    def upd_status():
        status_lb.configure(text=(
            f"Estado: {obs.status}\n"
            f"Escena: {obs.current_scene}\n"
            f"Grabando: {'SI' if obs.recording else 'NO'}\n"
            f"Streaming: {'SI' if obs.streaming else 'NO'}"
        ))
        tab.after(2000, upd_status)
    tab.after(2000, upd_status)

    c2 = mk(tab)
    c2.pack(fill="x", padx=14, pady=(0, 8))
    lb(c2, "Conexión", sz=12, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))
    ToolTip(c2, "Conecta con OBS Studio vía WebSocket.\nNecesitas tener OBS abierto con el plugin WebSocket (viene incluido en OBS 28+).")

    gf = ctk.CTkFrame(c2, fg_color="transparent")
    gf.pack(fill="x", padx=14, pady=(0, 4))
    gf.grid_columnconfigure(1, weight=1)
    gf.grid_columnconfigure(3, weight=1)

    lb(gf, "Host:", sz=10, col=MUT).grid(row=0, column=0, sticky="w")
    host_v = ctk.StringVar(value=obs._host)
    e1 = ctk.CTkEntry(gf, textvariable=host_v, font=("Consolas", 11), height=28)
    e1.grid(row=0, column=1, sticky="ew", padx=(5, 10), pady=2)

    lb(gf, "Puerto:", sz=10, col=MUT).grid(row=0, column=2, sticky="w")
    port_v = ctk.StringVar(value=str(obs._port))
    e2 = ctk.CTkEntry(gf, textvariable=port_v, font=("Consolas", 11), width=70, height=28)
    e2.grid(row=0, column=3, sticky="w", padx=(5, 0), pady=2)

    lb(gf, "Password:", sz=10, col=MUT).grid(row=1, column=0, sticky="w", pady=(4, 0))
    pw_v = ctk.StringVar(value=obs._password)
    pw_e = ctk.CTkEntry(gf, textvariable=pw_v, font=("Consolas", 11), show="*", height=28)
    pw_e.grid(row=1, column=1, columnspan=3, sticky="ew", padx=(5, 0), pady=(4, 0))

    def guardar_obs():
        obs.config(host_v.get().strip(), int(port_v.get().strip()), pw_e.get())
        from src.core.config import load_config, save_config
        cfg = load_config()
        cfg["OBS_HOST"] = host_v.get().strip()
        cfg["OBS_PORT"] = port_v.get().strip()
        cfg["OBS_PASSWORD"] = pw_e.get()
        save_config(cfg)
        self.log("[OBS] Config guardada")

    bf1 = ctk.CTkFrame(c2, fg_color="transparent")
    bf1.pack(fill="x", padx=14, pady=(6, 8))
    ctk.CTkButton(bf1, text="Guardar", font=("Segoe UI", 11),
                  fg_color="#475569", hover_color="#334155",
                  command=guardar_obs).pack(side="left", padx=(0, 6))
    ctk.CTkButton(bf1, text="Conectar", font=("Segoe UI", 11),
                  fg_color=GRN, text_color=GRN_T,
                  hover_color="#16a34a",
                  command=lambda: (guardar_obs(), obs.connect())).pack(side="left", padx=(0, 6))
    ctk.CTkButton(bf1, text="Desconectar", font=("Segoe UI", 11),
                  fg_color="#ef4444", text_color="#450a0a",
                  hover_color="#dc2626",
                  command=obs.disconnect).pack(side="left")

    c3 = mk(tab)
    c3.pack(fill="x", padx=14, pady=(0, 8))
    lb(c3, "Escenas", sz=12, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))

    esc_inner = ctk.CTkFrame(c3, fg_color=CARD, corner_radius=8)
    esc_inner.pack(fill="x", padx=14, pady=(0, 8))
    esc_content = ctk.CTkFrame(esc_inner, fg_color="transparent")
    esc_content.pack(fill="x", padx=8, pady=8)

    def refrescar_escenas():
        obs._refresh()
        for w in esc_content.winfo_children():
            w.destroy()
        if not obs.scenes:
            lb(esc_content, "(sin conexión)", sz=10, col=MUT).pack(anchor="w")
        else:
            for s in obs.scenes:
                name = s.get("sceneName", "") if isinstance(s, dict) else str(s)
                active = (name == obs.current_scene)
                btn = ctk.CTkButton(
                    esc_content,
                    text=f"{'▶ ' if active else '  '}{name}",
                    anchor="w", font=("Consolas", 11),
                    fg_color=PURP if active else "#334155",
                    hover_color="#6d28d9",
                    height=28,
                    command=lambda n=name: (obs.switch_scene(n), refrescar_escenas()),
                )
                btn.pack(fill="x", pady=2)
    tab.after(5000, refrescar_escenas)
    tab.after(1000, refrescar_escenas)

    c4 = mk(tab)
    c4.pack(fill="x", padx=14, pady=(0, 8))
    lb(c4, "Controles", sz=12, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))
    ToolTip(c4, "Inicia/detena la grabación y el streaming de OBS directamente desde la app.")

    bf2 = ctk.CTkFrame(c4, fg_color="transparent")
    bf2.pack(fill="x", padx=14, pady=(0, 10))
    ctk.CTkButton(bf2, text="Grabar / Detener", font=("Segoe UI", 12),
                  fg_color="#dc2626", text_color="#fecaca",
                  hover_color="#b91c1c",
                  command=obs.toggle_recording).pack(side="left", padx=(0, 8))
    ctk.CTkButton(bf2, text="Stream / Detener", font=("Segoe UI", 12),
                  fg_color="#2563eb", text_color="#bfdbfe",
                  hover_color="#1d4ed8",
                   command=obs.toggle_streaming).pack(side="left")

    ctk.CTkFrame(tab, height=10, fg_color="transparent").pack()
    return tab
