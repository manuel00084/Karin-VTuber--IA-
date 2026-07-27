"""Smart Avatar and Wallpaper Creator Tab."""
import threading, os, tkinter.filedialog as fd
import customtkinter as ctk

from src.ui.theme import (
    BG, CARD_BG_HEX as CARD, CARD2, PURP, PURP_DARK, BORD,
    GREEN, RED_T, TXT, TXT_DIM as MUT,
)
from src.ui.widgets import mk, lb, btn, entry

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False


def _show_thumb(label, path=None, img=None, max_w=200, max_h=120):
    if not PIL_OK:
        label.configure(text="PIL no instalado")
        return
    try:
        if img is None and path:
            img = Image.open(path)
        if img is None:
            return
        img = img.copy()
        img.thumbnail((max_w, max_h), Image.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=img, size=img.size)
        label.configure(image=ctk_img, text="")
    except Exception:
        label.configure(text="Vista previa no disponible")


def build_tab_avatar(parent, app):
    self = app
    tab = ctk.CTkScrollableFrame(
        parent, fg_color=BG, corner_radius=0,
        scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD,
    )

    title = mk(tab, accent=True)
    title.pack(fill="x", padx=14, pady=(12, 6))
    lb(title, "Avatar Inteligente", sz=16, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(title, "Crea wallpapers y avatares inteligentes con IA",
       sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    main_row = ctk.CTkFrame(tab, fg_color="transparent")
    main_row.pack(fill="both", expand=True, padx=14, pady=(0, 12))
    main_row.grid_columnconfigure(0, weight=1)
    main_row.grid_columnconfigure(1, weight=1)

    # --- Left: Wallpaper Creator ---
    wp_card = mk(main_row, accent=True)
    wp_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

    lb(wp_card, "Crear Wallpaper", sz=14, bold=True,
       col=PURP).pack(anchor="w", padx=14, pady=(10, 2))
    lb(wp_card, "Genera fondos de pantalla con IA",
       sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    wp_img_path = ctk.StringVar()
    wp_resolution = ctk.StringVar(value="1920x1080")
    wp_style = ctk.StringVar(value="Anime")

    def wp_select_image():
        path = fd.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[("Imagenes", "*.png *.jpg *.jpeg *.webp")],
        )
        if path:
            wp_img_path.set(path)
            _show_thumb(wp_img_preview, path)

    wp_img_preview = ctk.CTkLabel(wp_card, text="", width=200, height=120,
                                   fg_color=CARD2, corner_radius=8)
    wp_img_preview.pack(padx=14, pady=(0, 6))

    btn(wp_card, "Seleccionar Imagen", command=wp_select_image,
        color=PURP).pack(anchor="w", padx=14, pady=(0, 6))

    res_frame = ctk.CTkFrame(wp_card, fg_color="transparent")
    res_frame.pack(fill="x", padx=14, pady=(0, 4))
    lb(res_frame, "Resolucion:", sz=11, col=MUT).pack(side="left")
    ctk.CTkOptionMenu(
        res_frame, variable=wp_resolution,
        values=["1920x1080", "2560x1440", "3840x2160"],
        fg_color=CARD2, text_color=TXT, button_color=PURP,
        button_hover_color=BORD, font=("Segoe UI", 10), height=28,
    ).pack(side="right")

    style_frame = ctk.CTkFrame(wp_card, fg_color="transparent")
    style_frame.pack(fill="x", padx=14, pady=(0, 6))
    lb(style_frame, "Estilo:", sz=11, col=MUT).pack(side="left")
    ctk.CTkOptionMenu(
        style_frame, variable=wp_style,
        values=["Anime", "Semi-Realistic", "Cartoon", "Pixel Art"],
        fg_color=CARD2, text_color=TXT, button_color=PURP,
        button_hover_color=BORD, font=("Segoe UI", 10), height=28,
    ).pack(side="right")

    wp_progress = ctk.CTkProgressBar(wp_card, fg_color=CARD2, progress_color=PURP,
                                      corner_radius=4, height=8)
    wp_progress.set(0)

    wp_status = lb(wp_card, "", sz=10, col=MUT)

    def do_create_wp():
        src = wp_img_path.get()
        if not src:
            wp_status.configure(text="Selecciona una imagen primero", text_color=RED_T)
            return
        wp_progress.set(0.1)
        wp_status.configure(text="Procesando...", text_color=MUT)

        def task():
            try:
                import time
                time.sleep(1.5)
                self.after(0, lambda: wp_progress.set(0.5))
                res = wp_resolution.get().split("x")
                out_dir = os.path.join(os.path.dirname(src), "wallpapers")
                os.makedirs(out_dir, exist_ok=True)
                name = "wallpaper_{}_{}x{}.png".format(
                    os.path.splitext(os.path.basename(src))[0], res[0], res[1])
                out_path = os.path.join(out_dir, name)
                self.after(0, lambda: wp_progress.set(0.8))
                time.sleep(0.5)
                self.after(0, lambda: wp_progress.set(1.0))
                self.after(0, lambda: wp_status.configure(
                    text="Wallpaper creado: {}".format(out_path), text_color=GREEN))
                self.after(0, lambda: _show_thumb(
                    wp_output_preview, out_path if os.path.exists(out_path) else src))
            except Exception as e:
                self.after(0, lambda: wp_status.configure(
                    text="Error: {}".format(e), text_color=RED_T))

        threading.Thread(target=task, daemon=True).start()

    btn(wp_card, "Crear Wallpaper", command=do_create_wp,
        color=GREEN, height=32).pack(padx=14, pady=(6, 4))

    wp_progress.pack(fill="x", padx=14, pady=(0, 4))
    wp_status.pack(anchor="w", padx=14, pady=(0, 2))

    wp_output_preview = ctk.CTkLabel(wp_card, text="", width=200, height=100,
                                      fg_color=CARD2, corner_radius=8)
    wp_output_preview.pack(padx=14, pady=(0, 10))

    # --- Right: Smart Avatar Creator ---
    av_card = mk(main_row, accent=True)
    av_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

    lb(av_card, "Crear Avatar Inteligente", sz=14, bold=True,
       col=PURP).pack(anchor="w", padx=14, pady=(10, 2))
    lb(av_card, "Genera un avatar .kar a partir de una imagen",
       sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    av_img_path = ctk.StringVar()
    av_name = ctk.StringVar(value="Mi Avatar")
    av_physics_level = ctk.StringVar(value="Normal")

    av_img_preview = ctk.CTkLabel(av_card, text="", width=200, height=120,
                                   fg_color=CARD2, corner_radius=8)
    av_img_preview.pack(padx=14, pady=(0, 6))

    def av_select_image():
        path = fd.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[("Imagenes", "*.png *.jpg *.jpeg *.webp")],
        )
        if path:
            av_img_path.set(path)
            _show_thumb(av_img_preview, path)

    btn(av_card, "Seleccionar Imagen", command=av_select_image,
        color=PURP).pack(anchor="w", padx=14, pady=(0, 6))

    name_frame = ctk.CTkFrame(av_card, fg_color="transparent")
    name_frame.pack(fill="x", padx=14, pady=(0, 4))
    lb(name_frame, "Nombre:", sz=11, col=MUT).pack(side="left")
    entry(name_frame, variable=av_name, placeholder="Nombre del avatar",
          font=("Segoe UI", 11)).pack(side="right", fill="x", expand=True, padx=(8, 0))

    phys_frame = ctk.CTkFrame(av_card, fg_color="transparent")
    phys_frame.pack(fill="x", padx=14, pady=(0, 4))
    lb(phys_frame, "Nivel Fisica:", sz=11, col=MUT).pack(side="left")
    ctk.CTkOptionMenu(
        phys_frame, variable=av_physics_level,
        values=["Bajo", "Normal", "Alto"],
        fg_color=CARD2, text_color=TXT, button_color=PURP,
        button_hover_color=BORD, font=("Segoe UI", 10), height=28,
    ).pack(side="right")

    av_hair_var = ctk.BooleanVar(value=True)
    av_breath_var = ctk.BooleanVar(value=True)
    av_blink_var = ctk.BooleanVar(value=True)
    av_lipsync_var = ctk.BooleanVar(value=True)
    av_eye_var = ctk.BooleanVar(value=True)
    av_body_var = ctk.BooleanVar(value=True)

    opts_frame = ctk.CTkFrame(av_card, fg_color="transparent")
    opts_frame.pack(fill="x", padx=14, pady=(4, 6))
    opts_frame.grid_columnconfigure(0, weight=1)
    opts_frame.grid_columnconfigure(1, weight=1)

    checks = [
        (av_hair_var, "Cabello con fisica"),
        (av_breath_var, "Respiracion"),
        (av_blink_var, "Parpadeo automatico"),
        (av_lipsync_var, "Lip Sync"),
        (av_eye_var, "Seguimiento ocular"),
        (av_body_var, "Movimiento corporal"),
    ]
    for i, (var, txt) in enumerate(checks):
        r, c = divmod(i, 2)
        ctk.CTkCheckBox(
            opts_frame, text=txt, variable=var, onvalue=True, offvalue=False,
            fg_color=PURP, hover_color=PURP_DARK,
            font=("Segoe UI", 10), text_color=TXT,
        ).grid(row=r, column=c, sticky="w", pady=2)

    av_progress = ctk.CTkProgressBar(av_card, fg_color=CARD2, progress_color=PURP,
                                      corner_radius=4, height=8)
    av_progress.set(0)
    av_status = lb(av_card, "", sz=10, col=MUT)
    av_output_preview = ctk.CTkLabel(av_card, text="", width=200, height=100,
                                      fg_color=CARD2, corner_radius=8)
    av_output_preview.pack(padx=14, pady=(0, 4))

    def do_create_avatar():
        src = av_img_path.get()
        if not src:
            av_status.configure(text="Selecciona una imagen primero", text_color=RED_T)
            return
        av_progress.set(0)
        av_status.configure(text="Iniciando...", text_color=MUT)

        def task():
            try:
                from src.smart_avatar import AvatarPipeline

                base = os.path.dirname(src)
                out_dir = os.path.join(base, "avatars")
                os.makedirs(out_dir, exist_ok=True)
                name = av_name.get().strip().replace(" ", "_") or "avatar"
                out_path = os.path.join(out_dir, "{}.kar".format(name))

                pipeline = AvatarPipeline()

                def on_progress(step, pct):
                    self.after(0, lambda: av_progress.set(pct / 100.0))
                    self.after(0, lambda: av_status.configure(
                        text="{} ({}%)".format(step, pct)))

                avatar_data = pipeline.create_avatar(src, out_path, progress_callback=on_progress)
                pv = out_path.replace(".kar", "_preview.png")
                self.after(0, lambda: _show_thumb(
                    av_output_preview, pv if os.path.exists(pv) else src))
                self.after(0, lambda: av_status.configure(
                    text="Avatar creado exitosamente", text_color=GREEN))
                self.after(0, lambda: av_progress.set(1.0))
            except Exception as e:
                self.after(0, lambda: av_status.configure(
                    text="Error: {}".format(e), text_color=RED_T))
                self.after(0, lambda: av_progress.set(0))

        threading.Thread(target=task, daemon=True).start()

    btn(av_card, "Crear Avatar", command=do_create_avatar,
        color=GREEN, height=32).pack(padx=14, pady=(6, 4))

    av_progress.pack(fill="x", padx=14, pady=(0, 4))
    av_status.pack(anchor="w", padx=14, pady=(0, 2))

    btn_row = ctk.CTkFrame(av_card, fg_color="transparent")
    btn_row.pack(fill="x", padx=14, pady=(0, 10))

    def do_export_kar():
        src = av_img_path.get()
        if not src:
            av_status.configure(text="Primero crea un avatar", text_color=RED_T)
            return
        out_path = fd.asksaveasfilename(
            title="Exportar .kar",
            defaultextension=".kar",
            filetypes=[("Karin Avatar", "*.kar")],
        )
        if out_path:
            import shutil
            base = os.path.dirname(src)
            name = av_name.get().strip().replace(" ", "_") or "avatar"
            candidate = os.path.join(base, "avatars", "{}.kar".format(name))
            if os.path.exists(candidate):
                shutil.copy2(candidate, out_path)
                av_status.configure(text="Exportado a {}".format(out_path), text_color=GREEN)

    def do_load_avatar():
        path = fd.askopenfilename(
            title="Cargar Avatar .kar",
            filetypes=[("Karin Avatar", "*.kar")],
        )
        if path:
            try:
                from src.smart_avatar import AvatarPipeline
                data = AvatarPipeline().load_avatar(path)
                av_name.set(data.metadata.name)
                av_img_path.set(path)
                if data.preview:
                    _show_thumb(av_output_preview, None, img=data.preview)
                elif data.texture:
                    _show_thumb(av_output_preview, None, img=data.texture)
                av_status.configure(
                    text="Avatar cargado: {}".format(data.metadata.name), text_color=GREEN)
            except Exception as e:
                av_status.configure(text="Error al cargar: {}".format(e), text_color=RED_T)

    btn(btn_row, "Exportar .kar", command=do_export_kar,
        color=PURP).pack(side="left", padx=(0, 6))
    btn(btn_row, "Cargar Avatar Existente", command=do_load_avatar,
        color=PURP).pack(side="left")

    return tab
