"""Creditos Tab — help, about, and documentation."""
import customtkinter as ctk
import webbrowser, os

from src.ui.theme import (
    BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD,
    TXT, TXT_DIM as MUT,
)
from src.ui.widgets import mk, lb


def build_tab_creditos(parent, app):
    self = app
    tab = ctk.CTkScrollableFrame(parent, fg_color=BG, corner_radius=0,
                                  scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD)

    from src import PROJECT_ROOT
    APP_VERSION = "0.9.1-beta"
    APP_NAME = "Karin VTuber -IA-"

    card = mk(tab, accent=True)
    card.pack(fill="x", padx=14, pady=(12, 6))
    lb(card, f"{APP_NAME}  v{APP_VERSION}", sz=16, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(card, "Asistente VTuber con IA — Twitch, TTS, STT, Comentarista automático",
       sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 4))

    ctk.CTkFrame(card, height=1, fg_color="#2a2a3e").pack(fill="x", padx=14, pady=(6, 6))
    for label, url in [
        ("GitHub",                  "https://github.com/manuel00084"),
        ("Twitch",                  "https://www.twitch.tv/manuel0084"),
        ("Google Studio IA",        "https://aistudio.google.com/app/apikey"),
        ("Groq Console",            "https://console.groq.com/keys"),
        ("Cerebras Cloud",          "https://cloud.cerebras.ai"),
        ("Twitch Developer",        "https://dev.twitch.tv/console"),
    ]:
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=1)
        lb(row, label, sz=10, col=MUT, width=120).pack(side="left")
        lnk = lb(row, url, sz=10, col="#818cf8", cursor="hand2")
        lnk.pack(side="left", padx=(8, 0))
        lnk.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
    ctk.CTkFrame(card, height=6, fg_color="transparent").pack()

    btn_row = ctk.CTkFrame(card, fg_color="transparent")
    btn_row.pack(fill="x", padx=14, pady=(0, 10))
    ctk.CTkButton(btn_row, text="📖  Abrir Manual Completo", fg_color=PURP, text_color="#f3e8ff",
                  height=36, corner_radius=8, hover_color="#a855f7",
                  command=lambda: webbrowser.open(
                      "file:///" + os.path.join(PROJECT_ROOT, "tutorial.html").replace("\\", "/"))).pack()

    guide = mk(tab, accent=True)
    guide.pack(fill="x", padx=14, pady=(0, 6))
    lb(guide, "📖  Guía rápida", sz=12, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(10, 2))
    items = [
        ("📊  Panel", "Control principal — perfiles, PTT, actividad en vivo y guardado rápido"),
        ("🎧  Audio", "Selecciona dispositivos: Speaker (Bot), IA Voz (TTS) y Monitor (escucha)"),
        ("🗣  Personalidad", "Perfil de la IA + Perfil del Streamer como contexto del prompt"),
        ("🤖  Bot Speaker", "Comandos !sp / !spm. Sube MP3 y asígnales un comando personalizado"),
        ("💬  Chat Bot IA", "IA que responde con voz en Twitch + Comentarista automático del juego"),
        ("🔑  API Keys", "Groq (comentarista), Cerebras (chat), Google Studio (vision/chat)"),
    ]
    for icon_title, desc in items:
        row = ctk.CTkFrame(guide, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=2)
        lb(row, icon_title, sz=11, bold=True, col=TXT, width=120).pack(side="left")
        lb(row, desc, sz=9, col=MUT).pack(side="left", padx=(8, 0))
    ctk.CTkFrame(guide, height=6, fg_color="transparent").pack()

    pf = mk(tab)
    pf.pack(fill="x", padx=14, pady=(0, 6))
    lb(pf, "👤  Perfiles de IA y Streamer", sz=12, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(10, 2))
    pf_info = [
        "Perfil de la IA — Nombre, edad, género, altura, gustos, frases típicas, cumpleaños, signo, trabajo",
        "Perfil del Streamer / Player — Mismos campos: nombre, apellido, edad, género, cumpleaños, signo, altura, trabajo",
        "Ambos perfiles se concatenan automáticamente como contexto ANTES del prompt de personalidad",
        "La IA usa estos datos para saber quién es ella y quién es su compañero/player",
        "Cada perfil tiene su botón 💾 Guardar para persistir los datos en config.txt",
        "Los campos se cargan automáticamente al iniciar la aplicación",
    ]
    for t in pf_info:
        lb(pf, f"•  {t}", sz=9, col=MUT).pack(anchor="w", padx=14, pady=1)
    ctk.CTkFrame(pf, height=6, fg_color="transparent").pack()

    modes = mk(tab)
    modes.pack(fill="x", padx=14, pady=(0, 6))
    lb(modes, "🎮  Comentarista automático", sz=12, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(10, 2))
    lb(modes, "Los módulos se activan con switches y se combinan entre sí:", sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    mode_details = [
        ("📖 OCR",
         "Lectura de texto en pantalla con RapidOCR. "
         "Pre-procesa la imagen: upscale 2x, eliminación de glow, CLAHE y sharpen. "
         "Filtra detecciones pequeñas (<4% de la altura) y texto inválido (<4 caracteres, <30% letras). "
         "Si detecta <2 resultados a resolución reducida, reintenta a resolución completa (720p). "
         "El texto se narra con prefijo aleatorio: 'Veo en pantalla:', 'Pone:', 'Dice:', etc."),
        ("👁 CLIP Vision (MobileCLIP-S2)",
         "Análisis visual con MobileCLIP-S2 en CPU. "
         "Reemplaza OpenCV+reglas manuales por zero-shot classification: "
         "detecta personajes, enemigos, escenarios, efectos (fuego, hielo, explosión) "
         "y estados del juego (combate, victoria, muerte). Sin APIs externas."),
        ("🎭 Karin Animadora",
         "Genera comentarios animados y dinámicos basados en la detección visual. "
         "Combina datos de OCR + CLIP Vision para producir reacciones más vivas. "
         "Usa la IA de texto (proveedor seleccionado en dropdown) para generar las frases."),
        ("🟢 Groq Vision",
         "Captura la pantalla y envía la imagen a Groq para descripción visual. "
         "Modelo: meta-llama/llama-4-scout-17b-16e-instruct. "
         "Incluye OCR + contexto del juego en el prompt. "
         "Tasa adaptable: 5-15s entre capturas. "
         "Usa la API Key de Groq (gsk_...)."),
        ("🔵 Google Vision",
         "Captura la pantalla y envía la imagen a Gemini para descripción detallada. "
         "Cadena de fallback automática: "
         "gemini-2.0-flash → gemini-2.0-flash-001 → gemini-2.5-flash. "
         "Incluye OCR + contexto del juego. "
         "Usa la API Key de Google Studio (AIza...)."),
    ]
    for icon_title, desc in mode_details:
        row = ctk.CTkFrame(modes, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=2)
        lb(row, icon_title, sz=11, bold=True, col=TXT, width=120).pack(side="left", anchor="n")
        lb(row, desc, sz=9, col=MUT, wraplength=400).pack(side="left", padx=(8, 0), fill="x", expand=True)
    lb(modes, "💡 Los módulos se pueden combinar (ej: OCR + Groq Vision). Al togglear, se reinicia el servicio.",
       sz=9, col=MUT).pack(anchor="w", padx=14, pady=(6, 1))
    ctk.CTkFrame(modes, height=6, fg_color="transparent").pack()

    prov = mk(tab)
    prov.pack(fill="x", padx=14, pady=(0, 6))
    lb(prov, "🤖  Proveedores de IA", sz=12, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(10, 2))
    lb(prov, "Cada proveedor tiene su propia API Key y modelos disponibles:", sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    prov_details = [
        ("🟢 Groq",
         "Texto: llama-3.3-70b-versatile, deepseek-r1-distill-llama-70b, gemma2-9b-it. "
         "Visión: llama-4-scout-17b, llama-4-maverick-17b. "
         "Usado para: Comentarista, PTT. "
         "Modelos auto-descubiertos via API. "
         "Web: console.groq.com/keys — Key: gsk_..."),
        ("🟡 Cerebras",
         "Texto: gpt-oss-120b. "
         "Sin visión. "
         "Usado para: Chat Bot IA, PTT, Twitch. "
         "Web: cloud.cerebras.ai — Key: csk_..."),
        ("🔴 Google Studio",
         "Texto + Visión: gemini-2.0-flash, gemini-2.5-flash. "
         "Usado para: Chat Bot IA, Google Vision. "
         "Web: aistudio.google.com/app/apikey — Key: AIza..."),
    ]
    for icon_title, desc in prov_details:
        row = ctk.CTkFrame(prov, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=2)
        lb(row, icon_title, sz=11, bold=True, col=TXT, width=40).pack(side="left", anchor="n")
        lb(row, desc, sz=9, col=MUT, wraplength=460).pack(side="left", padx=(4, 0), fill="x", expand=True)
    lb(prov, "💡 Fallback automático: si un proveedor falla (429 rate limit), prueba el siguiente en cadena.",
       sz=9, col=MUT).pack(anchor="w", padx=14, pady=(2, 1))
    lb(prov, "💡 Las respuestas AI incluyen emoción consciente [alegre][triste][enojado][sorpresa][neutro] para TTS + avatar.",
       sz=9, col=MUT).pack(anchor="w", padx=14, pady=(2, 6))
    ctk.CTkFrame(prov, height=6, fg_color="transparent").pack()

    feat = mk(tab)
    feat.pack(fill="x", padx=14, pady=(0, 6))
    lb(feat, "🆕  Novedades v0.9.1", sz=12, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(10, 2))
    feat_items = [
        "Rotación automática entre proveedores IA — Groq → Cerebras → Google si hay rate limit",
        "Emoción consciente en respuestas AI: [alegre][triste][enojado][sorpresa][neutro] para TTS animado",
        "Log diario con rotación en logs/karin-YYYY-MM-DD.log",
        "OBS se conecta automáticamente al inicio si hay credenciales configuradas",
        "Cierre graceful — detiene audio, descarga plugins y desconecta OBS al salir",
        "Clave de encriptación configurable via KARIN_ENCRYPTION_KEY en entorno",
        "Auto-descubrimiento de modelos IA via API (/v1/models) con caché de 1 hora",
    ]
    for t in feat_items:
        lb(feat, f"•  {t}", sz=9, col=MUT).pack(anchor="w", padx=14, pady=1)
    ctk.CTkFrame(feat, height=6, fg_color="transparent").pack()

    audio = mk(tab)
    audio.pack(fill="x", padx=14, pady=(0, 6))
    lb(audio, "🔊  Sistema de Audio", sz=12, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(10, 2))
    audio_details = [
        "Speaker (Bot) — Altavoz principal para comandos !sp / !spm del Bot Speaker en Twitch",
        "IA Voz (TTS) — Dispositivo donde se reproduce la voz del Comentarista IA y Chat Bot",
        "Monitor — Segundo dispositivo opcional: la IA se escucha en Speaker + Monitor simultáneamente",
        "Volumen fijo 2.0. Normalización al 85% para evitar distorsión",
        "Push-To-Talk (PTT) — Mantén F9 (configurable) para hablar, se envía a la IA y responde con voz",
        "Edge TTS — Voces neuronales en español: Dalia, Dario, Lia, Elvira, Emilia, etc.",
        "TTS ajusta tono según emoción: feliz (+15%), enojado (-5%), sorpresa (+10%), triste (-10%)",
    ]
    for t in audio_details:
        lb(audio, f"•  {t}", sz=9, col=MUT).pack(anchor="w", padx=14, pady=1)
    ctk.CTkFrame(audio, height=6, fg_color="transparent").pack()

    req = mk(tab)
    req.pack(fill="x", padx=14, pady=(0, 6))
    lb(req, "⚙️  Requisitos", sz=12, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(10, 2))
    reqs = [
        "Python 3.10 o superior",
        "API Key de al menos un proveedor: Groq (gsk_), Cerebras (csk_) o Google Studio (AIza)",
        "Cuenta de desarrollador en Twitch (dev.twitch.tv) para OAuth y Bot",
        "Modelo Vosk pequeño español (vosk-model-small-es-0.42) para STT / PTT",
        "Windows 10+ (dxcam para captura de pantalla rápida)",
        "Conexión a internet para APIs de IA y TTS",
    ]
    for r in reqs:
        lb(req, f"•  {r}", sz=9, col=MUT).pack(anchor="w", padx=14, pady=1)
    ctk.CTkFrame(req, height=6, fg_color="transparent").pack()

    legal = mk(tab)
    legal.pack(fill="x", padx=14, pady=(0, 6))
    lb(legal, "⚖️  Licencia", sz=12, bold=True, col=PURP).pack(anchor="w", padx=12, pady=(10, 2))
    lb(legal, "Apache License 2.0", sz=10, col=MUT).pack(anchor="w", padx=12, pady=(2, 0))
    a_link = lb(legal, "apache.org/licenses/LICENSE-2.0", sz=10, col="#818cf8", cursor="hand2")
    a_link.pack(anchor="w", padx=12, pady=(0, 2))
    a_link.bind("<Button-1>", lambda e: webbrowser.open("http://www.apache.org/licenses/LICENSE-2.0"))
    lb(legal, "Desarrollado por Manuel0084", sz=10, col=MUT).pack(anchor="w", padx=12, pady=(2, 0))
    lb(legal, "Copyright 2024-2026", sz=10, col=MUT).pack(anchor="w", padx=12, pady=(0, 6))

    tp = mk(tab)
    tp.pack(fill="x", padx=14, pady=(0, 12))
    lb(tp, "📦  Terceros", sz=12, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(10, 2))
    lb(tp, "Software y modelos de terceros con sus respectivas licencias:",
       sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 4))
    tg = ctk.CTkFrame(tp, fg_color="transparent")
    tg.pack(fill="x", padx=14, pady=(4, 8))
    tg.grid_columnconfigure((0, 1), weight=1)
    third_party = [
        ("Vosk", "Apache 2.0"),
        ("Edge TTS", "Microsoft"),
        ("CustomTkinter", "MIT"),
        ("OpenCV", "Apache 2.0"),
        ("TwitchIO", "MIT"),
        ("RapidOCR (ONNX)", "Apache 2.0"),
        ("ONNX Runtime", "MIT"),
        ("dxcam", "MIT"),
        ("Groq API", "Propietaria"),
        ("Cerebras API", "Propietaria"),
        ("Google Gemini API", "Propietaria"),
        ("Pillow", "Historical"),
    ]
    for i, (lib, lic) in enumerate(third_party):
        r, c = divmod(i, 2)
        lb(tg, f"• {lib}  —  {lic}", sz=10, col=MUT).grid(row=r, column=c, sticky="w", pady=1, padx=(0, 8))

    return tab
