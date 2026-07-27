"""Audio Tab — device selection and pitch control."""
import customtkinter as ctk

from src.ui.theme import (
    BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD,
    GRN, GRN_T,
    TXT, TXT_DIM as MUT,
)
from src.ui.widgets import mk, lb, ToolTip, cb


def build_tab_audio(parent, app):
    self = app
    tab = ctk.CTkScrollableFrame(parent, fg_color=BG, corner_radius=0,
                                  scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD)

    c = mk(tab, accent=True)
    c.pack(fill="x", padx=14, pady=(12, 6))
    lb(c, "🔊  Dispositivos de audio", sz=12, bold=True).pack(anchor="w", padx=14, pady=(10, 4))

    def _hacer_mn_vals():
        return ["(Ninguno)"] + self.dev_names

    def _monitor_cambio(*_):
        from src.audio.audio import set_monitor_device
        idx = self.mn2.get()
        if idx in ("(Ninguno)", ""):
            set_monitor_device(None)
        else:
            mid = next((i for n, i in self.devices if n == idx), None)
            set_monitor_device(mid)

    for txt, attr, default, tip in [
        ("Bot Speaker", "sp2", self._sp_default, "Dispositivo donde Karin reproduce TTS y sonidos del bot (!sp, !spm)."),
        ("IA Voz", "ia2", self._ia_default, "Dispositivo que usa la IA para hablar por voz (PTT, Push-to-Talk)."),
        ("Monitor", "mn2", self._mn_default, "Dispositivo de escucha para grabar audio del sistema. Puedes dejarlo en Ninguno."),
    ]:
        lbl = lb(c, txt, sz=10, col=MUT)
        lbl.pack(anchor="w", padx=14, pady=(4, 0))
        ToolTip(lbl, tip)
        vals = _hacer_mn_vals() if "Monitor" in txt else self.dev_names
        bx = cb(c, vals); bx.pack(fill="x", padx=14, pady=(0, 4))
        if default in vals:
            bx.set(default)
        else:
            bx.set(vals[0])
        setattr(self, attr, bx)
        if "Monitor" in txt:
            bx.configure(command=_monitor_cambio)

    ctk.CTkFrame(c, height=6, fg_color="transparent").pack()

    # ── Pitch shift slider (solo monitor) ──
    pf_frame = ctk.CTkFrame(c, fg_color="transparent")
    pf_frame.pack(fill="x", padx=14, pady=(4, 0))
    lb(pf_frame, "🎵  Tono (semitonos)", sz=10, col=MUT).pack(anchor="w")
    val_lb = lb(pf_frame, "0", sz=11, bold=True, col=PURP)
    val_lb.pack(anchor="w", pady=(2, 0))
    pitch_slider = ctk.CTkSlider(pf_frame, from_=-12, to=12, number_of_steps=24,
                                 fg_color=CARD2, button_color=PURP,
                                 progress_color=PURP, height=16)
    pitch_slider.set(0)
    pitch_slider.pack(fill="x", pady=(4, 2))
    lb(pf_frame, "Afecta solo al Monitor (stream/grabación). -12 = octava abajo, +12 = octava arriba",
       sz=9, col=MUT).pack(anchor="w")

    def _pitch_cambio(val):
        sem = round(val)
        pitch_slider.set(sem)
        val_lb.configure(text=f"{sem:+d}")
        from src.audio.audio import set_pitch
        set_pitch(sem)

    pitch_slider.configure(command=_pitch_cambio)

    ctk.CTkFrame(c, height=6, fg_color="transparent").pack()

    # ── EQ 5 bandas (solo monitor) ──
    eq_frame = ctk.CTkFrame(c, fg_color="transparent")
    eq_frame.pack(fill="x", padx=14, pady=(4, 0))
    lb(eq_frame, "🎚  Ecualizador (solo monitor)", sz=10, col=MUT).pack(anchor="w")

    eq_labels = ["Graves\n80Hz", "Me-Graves\n300Hz", "Medios\n1kHz", "Me-Agudos\n4kHz", "Agudos\n12kHz"]
    eq_sliders = []
    eq_val_lbs = []
    eq_grid = ctk.CTkFrame(eq_frame, fg_color="transparent")
    eq_grid.pack(fill="x", pady=(4, 0))
    for i in range(5):
        eq_grid.grid_columnconfigure(i, weight=1)
        i_frame = ctk.CTkFrame(eq_grid, fg_color="transparent")
        i_frame.grid(row=0, column=i, padx=2)
        lb(i_frame, eq_labels[i], sz=8, col=MUT).pack(anchor="center")
        vl = lb(i_frame, "0", sz=10, bold=True, col=PURP)
        vl.pack(anchor="center", pady=(1, 0))
        eq_val_lbs.append(vl)
        sl = ctk.CTkSlider(i_frame, from_=-12, to=12, number_of_steps=24,
                           fg_color=CARD2, button_color=PURP,
                           progress_color=PURP, height=14, width=80)
        sl.set(0)
        sl.pack(pady=(2, 0))
        eq_sliders.append(sl)

    def _eq_cambio(i, val):
        db = round(val)
        eq_sliders[i].set(db)
        eq_val_lbs[i].configure(text=f"{db:+d}")
        from src.audio.audio import set_eq_gain
        set_eq_gain(i, db)

    for i, sl in enumerate(eq_sliders):
        sl.configure(command=lambda v, idx=i: _eq_cambio(idx, v))

    lb(eq_frame, "-12dB a +12dB por banda. Mejora claridad y calidez de la voz TTS.",
       sz=9, col=MUT).pack(anchor="w", pady=(2, 0))

    ctk.CTkFrame(c, height=6, fg_color="transparent").pack()

    def guardar_audio_devices():
        from src.core.config import load_config, save_config
        cfg = load_config()
        if hasattr(self, 'sp2'):
            idx = self.sp2.get()
            cfg["SPEAKER_DEVICE"] = str(self.dev_names.index(idx)) if idx in self.dev_names else "0"
        if hasattr(self, 'ia2'):
            idx = self.ia2.get()
            cfg["IA_DEVICE"] = str(self.dev_names.index(idx) if idx in self.dev_names else 0)
        if hasattr(self, 'mn2'):
            idx = self.mn2.get()
            if idx in ("(Ninguno)", ""):
                cfg.pop("MONITOR_DEVICE", None)
            else:
                cfg["MONITOR_DEVICE"] = str(self.dev_names.index(idx) if idx in self.dev_names else 0)
        cfg["MONITOR_PITCH"] = str(round(pitch_slider.get()))
        for i, sl in enumerate(eq_sliders):
            cfg[f"MONITOR_EQ_{i}"] = str(round(sl.get()))
        save_config(cfg)
        self.log(f"✅  Dispositivos guardados: Speaker={cfg.get('SPEAKER_DEVICE','?')}, IA={cfg.get('IA_DEVICE','?')}, Monitor={cfg.get('MONITOR_DEVICE','ninguno')}, Pitch={cfg.get('MONITOR_PITCH','0')}")

    ctk.CTkButton(c, text="💾 Guardar dispositivos", fg_color=GRN, text_color=GRN_T,
                  height=30, corner_radius=8, hover_color="#10b981",
                  command=guardar_audio_devices).pack(padx=14, pady=(0, 10))

    self._plugin_manager.emit("audio_tab", tab)
    return tab
