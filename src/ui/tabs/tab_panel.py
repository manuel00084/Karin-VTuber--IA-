"""Panel Tab — main control panel with log."""
import customtkinter as ctk

from src.ui.theme import BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD, TXT, LOGBG
from src.ui.widgets import mk, lb, ToolTip


def build_tab_panel(parent, app):
    self = app
    tab = ctk.CTkScrollableFrame(parent, fg_color=BG, corner_radius=0)

    lc = mk(tab, accent=True)
    lc.pack(fill="x", padx=14, pady=(12, 6))
    lb(lc, "📋  Actividad", sz=11, bold=True).pack(anchor="w", padx=14, pady=(10, 2))

    search_frame = ctk.CTkFrame(lc, fg_color="transparent", height=28)
    search_frame.pack(fill="x", padx=14, pady=(0, 4))

    search_var = ctk.StringVar()
    search_entry = ctk.CTkEntry(
        search_frame, textvariable=search_var,
        placeholder_text="🔍  Filtrar log...",
        font=("Segoe UI", 10),
        height=26, border_width=0,
        fg_color="#0a0a1a", text_color="#ccc",
    )
    search_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))

    def apply_filter(*_):
        q = search_var.get().strip().lower()
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        for line in _log_buffer:
            if not q or q in line.lower():
                self.log_box.insert("end", line + "\n")
        self.log_box.configure(state="normal")
        self.log_box.see("end")

    search_var.trace_add("write", apply_filter)

    clear_btn = ctk.CTkButton(
        search_frame, text="✕", width=26, height=26,
        command=lambda: search_var.set(""),
        fg_color=CARD2, hover_color=PURP,
        text_color="#fff", font=("Segoe UI", 10),
        corner_radius=4, border_width=0,
    )
    clear_btn.pack(side="right", padx=(2, 0))

    def clear_log():
        search_var.set("")
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="normal")
        _log_buffer.clear()

    clear_all_btn = ctk.CTkButton(
        search_frame, text="🗑", width=26, height=26,
        command=clear_log,
        fg_color=CARD2, hover_color="#e74c3c",
        text_color="#fff", font=("Segoe UI", 10),
        corner_radius=4, border_width=0,
    )
    clear_all_btn.pack(side="right", padx=(2, 0))

    self.log_box = ctk.CTkTextbox(lc, height=150, font=("Consolas", 11),
                                  fg_color=LOGBG, text_color="#7dd3fc",
                                  border_width=0, corner_radius=6)
    self.log_box.pack(fill="x", padx=14, pady=(0, 12))

    _log_buffer = []

    orig_log = self.log

    def log_with_buffer(text):
        _log_buffer.append(text)
        if len(_log_buffer) > 1000:
            _log_buffer[:] = _log_buffer[-500:]
        q = search_var.get().strip().lower()
        if not q or q in text.lower():
            orig_log(text)

    self.log = log_with_buffer

    # ── Profiles ──
    prof_card = mk(tab, accent=True)
    prof_card.pack(fill="x", padx=14, pady=(6, 6))
    lb(prof_card, "💾  Perfiles de configuración", sz=11, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lbl_prof = lb(prof_card, "Guarda y carga configuraciones completas (devices, keys, ajustes).", sz=9, col="#64748b")
    lbl_prof.pack(anchor="w", padx=14, pady=(0, 2))
    ToolTip(lbl_prof, "Guarda todo tu setup actual (dispositivos, API keys, ajustes del bot) como perfil.\nPuedes tener varios perfiles y cambiar entre ellos rápido.")

    prof_inner = ctk.CTkFrame(prof_card, fg_color="transparent")
    prof_inner.pack(fill="x", padx=14, pady=(4, 10))

    def refresh_profile_list():
        from src.core.secrets_manager import list_profiles, save_profile, load_profile, delete_profile, export_profile, import_profile
        profiles = list_profiles()
        menu = [f"{p}" for p in profiles] if profiles else ["(sin perfiles)"]
        return profiles, menu

    prof_var = ctk.StringVar()

    def prof_load():
        from src.core.secrets_manager import list_profiles, load_profile
        name = prof_var.get()
        if name:
            app.log(f"💾  Cargando perfil '{name}'...")
            if load_profile(name):
                app.log(f"✅  Perfil '{name}' cargado. Reiniciá la app para aplicar cambios.")
            else:
                app.log(f"❌  Error cargando perfil '{name}'")

    def prof_save():
        from src.core.secrets_manager import save_profile
        dialog = ctk.CTkInputDialog(title="Guardar perfil", text="Nombre del perfil:")
        name = dialog.get_input()
        if name and name.strip():
            save_profile(name.strip())
            app.log(f"✅  Perfil '{name.strip()}' guardado")
            refresh_profile_list()
        else:
            app.log("⚠  Nombre de perfil inválido")

    def prof_delete():
        from src.core.secrets_manager import delete_profile
        name = prof_var.get()
        if name:
            delete_profile(name)
            app.log(f"🗑  Perfil '{name}' eliminado")
            refresh_profile_list()

    profiles_frame = ctk.CTkFrame(prof_inner, fg_color="transparent")
    profiles_frame.pack(fill="x")

    prof_opt = ctk.CTkOptionMenu(
        profiles_frame, variable=prof_var,
        values=["(sin perfiles)"],
        fg_color=CARD, button_color=PURP, button_hover_color=BORD,
        text_color=TXT, font=("Segoe UI", 10),
        dropdown_fg_color=CARD, dropdown_text_color=TXT,
        dropdown_hover_color=PURP,
    )
    prof_opt.pack(side="left", fill="x", expand=True, padx=(0, 4))

    def refresh_profile_list():
        from src.core.secrets_manager import list_profiles
        p = list_profiles()
        if p:
            prof_opt.configure(values=p)
            if prof_var.get() not in p:
                prof_var.set(p[0])
        else:
            prof_opt.configure(values=["(sin perfiles)"])
            prof_var.set("(sin perfiles)")

    for txt, cmd, tip in [("💾", prof_save, "Guardar configuración actual como perfil nuevo"), ("📂", prof_load, "Cargar perfil seleccionado"), ("🗑", prof_delete, "Eliminar perfil seleccionado")]:
        btn = ctk.CTkButton(
            profiles_frame, text=txt, width=30, height=28,
            command=cmd,
            fg_color=CARD2, hover_color=PURP,
            text_color="#fff", font=("Segoe UI", 11),
            corner_radius=4, border_width=0,
        )
        btn.pack(side="left", padx=2)
        ToolTip(btn, tip)

    def prof_export():
        from src.core.secrets_manager import export_profile
        import tkinter.filedialog as fd
        name = prof_var.get()
        if name:
            path = fd.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON", "*.json")],
                initialfile=f"{name}.json",
            )
            if path and export_profile(name, path):
                app.log(f"✅  Perfil exportado a {path}")

    def prof_import():
        from src.core.secrets_manager import import_profile
        import tkinter.filedialog as fd
        path = fd.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            name = import_profile(path)
            if name:
                app.log(f"✅  Perfil importado como '{name}'")
                refresh_profile_list()

    for txt, cmd, tip in [("📤", prof_export, "Exportar perfil a archivo JSON"), ("📥", prof_import, "Importar perfil desde archivo JSON")]:
        btn = ctk.CTkButton(
            profiles_frame, text=txt, width=30, height=28,
            command=cmd,
            fg_color=CARD2, hover_color=PURP,
            text_color="#fff", font=("Segoe UI", 11),
            corner_radius=4, border_width=0,
        )
        btn.pack(side="left", padx=2)
        ToolTip(btn, tip)

    refresh_profile_list()

    self._build_prompt(self._selected_prompt_file)

    return tab
