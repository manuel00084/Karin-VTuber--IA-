"""API Key Tab — manage API keys for AI providers."""
import customtkinter as ctk
import webbrowser, requests

from src.ui.theme import (
    BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD,
    GRN, GRN_T, RED, RED_T_LIGHT as RED_T,
    TXT, TXT_DIM as MUT,
)
from src.ui.widgets import mk, lb, ToolTip


def build_tab_api_key(parent, app, frame=None):
    self = app
    tab = frame or ctk.CTkScrollableFrame(parent, fg_color=BG, corner_radius=0,
                                           scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD)

    from src.core.config import load_config as _lc
    config = _lc()

    c = mk(tab, accent=True)
    c.pack(fill="x", padx=14, pady=(12, 6))
    lb(c, "🔑  API Keys", sz=13, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(c, "Configura las claves de los proveedores de IA", sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    def toggle_key(entry):
        current = entry.cget("show")
        entry.configure(show="" if current == "*" else "*")

    def test_api(provider, key):
        if not key:
            self.log(f"❌  Ingresa una API Key primero")
            return
        if provider == "cerebras":
            try:
                r = requests.post("https://api.cerebras.ai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={"model": "llama3.1-8b", "messages": [{"role": "user", "content": "test"}], "max_tokens": 5},
                    timeout=15)
                self.log(f"✅  Cerebras API responde: {r.status_code}")
            except Exception as e:
                self.log(f"❌  Cerebras error: {e}")
        elif provider == "groq":
            try:
                r = requests.get("https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {key}"}, timeout=10)
                self.log(f"✅  Groq API responde: {r.status_code}")
            except Exception as e:
                self.log(f"❌  Groq error: {e}")
        elif provider == "google_studio":
            try:
                url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + key
                r = requests.post(url,
                    json={"contents": [{"parts": [{"text": "test"}]}]},
                    timeout=15)
                self.log(f"✅  Google Studio IA API responde: {r.status_code}")
            except Exception as e:
                self.log(f"❌  Google Studio IA error: {e}")
        elif provider == "local":
            test_local_ai()

    def guardar_cere():
        value = self.cere_key_entry.get().strip()
        if not value:
            self.log("❌  Ingresa una API Key válida")
            return
        if not (value.startswith("csk-") or value.startswith("csk_")):
            self.log("❌  Cerebras API Key debe empezar con 'csk-'")
            return
        from src.core.config import load_config, save_config
        cfg = load_config()
        cfg["CEREBRAS_API_KEY"] = value
        save_config(cfg)
        self.log(f"✅  CEREBRAS_API_KEY guardada correctamente")

    def guardar_groq():
        value = self.groq_key_entry.get().strip()
        if not value:
            self.log("❌  Ingresa una API Key válida")
            return
        if not value.startswith("gsk_"):
            self.log("❌  Groq API Key debe empezar con 'gsk_'")
            return
        from src.core.config import load_config, save_config
        cfg = load_config()
        cfg["GROQ_API_KEY"] = value
        save_config(cfg)
        self.log(f"✅  API Key de Groq guardada correctamente")

    def guardar_google():
        value = self.google_key_entry.get().strip()
        if not value:
            self.log("❌  Ingresa una API Key válida")
            return
        if not value.startswith("AIza"):
            self.log("❌  Google Studio API Key debe empezar con 'AIza'")
            return
        from src.core.config import load_config, save_config
        cfg = load_config()
        cfg["GOOGLE_STUDIO_API_KEY"] = value
        save_config(cfg)
        self.log(f"✅  Google Studio IA API Key guardada correctamente")

    tips = {
        "cerebras": "Motor de IA gratuito para chat, respuesta de comandos Twitch y Push-to-Talk.",
        "groq": "Motor de IA con visión. Usa el Comentarista para analizar gameplay.",
        "google_studio": "Motor de IA de Google. Alternativa a Cerebras/Groq.",
    }
    for provider, icon, title, usage, entry_attr, placeholder_key, cfg_key, link_url, test_fn in [
        ("cerebras", "🟡", "Cerebras", "Chat Bot, PTT, Twitch",
         "cere_key_entry", "csk_...", "CEREBRAS_API_KEY",
         "https://cloud.cerebras.ai", "cerebras"),
        ("groq", "🔵", "Groq", "Comentarista (Vision IA)",
         "groq_key_entry", "gsk_...", "GROQ_API_KEY",
         "https://console.groq.com", "groq"),
        ("google_studio", "🔴", "Google Studio IA", "Chat Bot, Vision IA",
         "google_key_entry", "AIza...", "GOOGLE_STUDIO_API_KEY",
         "https://aistudio.google.com/app/apikey", "google_studio"),
    ]:
        card = mk(c)
        card.pack(fill="x", padx=14, pady=(0, 8))
        title_lbl = lb(card, f"{icon}  {title} — {usage}", sz=12, bold=True, col=TXT)
        title_lbl.pack(anchor="w", padx=14, pady=(10, 4))
        ToolTip(title_lbl, tips[provider])

        entry = ctk.CTkEntry(card, placeholder_text=placeholder_key,
                            font=("Consolas", 12), show="*",
                            fg_color=CARD, text_color=TXT, border_color=BORD)
        entry.pack(fill="x", padx=14, pady=(0, 4))
        val = config.get(cfg_key, "")
        if val:
            entry.insert(0, val)
        setattr(self, entry_attr, entry)

        bf = ctk.CTkFrame(card, fg_color="transparent")
        bf.pack(fill="x", padx=14, pady=(4, 4))
        bf.grid_columnconfigure((0, 1, 2), weight=1)

        guardar_fn = {"cerebras": guardar_cere, "groq": guardar_groq, "google_studio": guardar_google}[provider]

        ctk.CTkButton(bf, text="👁", fg_color=CARD2, text_color=TXT,
                      command=lambda e=entry: toggle_key(e),
                      height=30, corner_radius=8, width=40).grid(row=0, column=0, padx=(0, 4))
        ctk.CTkButton(bf, text="💾 Guardar", fg_color=GRN, text_color=GRN_T,
                      command=guardar_fn,
                      height=30, corner_radius=8, hover_color="#10b981").grid(row=0, column=1, padx=2)
        ctk.CTkButton(bf, text="🧪 Test", fg_color=PURP, text_color="#f3e8ff",
                      command=lambda p=test_fn, e=entry: test_api(p, e.get()),
                      height=30, corner_radius=8).grid(row=0, column=2, padx=(4, 0))

        link = lb(card, f"🌐  {link_url}", sz=10, col="#818cf8", cursor="hand2")
        link.pack(anchor="w", padx=14, pady=(2, 4))
        link.bind("<Button-1>", lambda e, u=link_url: webbrowser.open(u))

        status = config.get(cfg_key, "")
        if status and len(status) > 5:
            lb(card, f"✅ Guardada (****{status[-6:]})", sz=10, col=GRN_T).pack(anchor="w", padx=14, pady=(0, 8))
        else:
            lb(card, "❌ No configurada", sz=10, col=RED_T).pack(anchor="w", padx=14, pady=(0, 8))

    # ── Local AI ──
    local_card = mk(tab)
    local_card.pack(fill="x", padx=14, pady=(0, 8))
    lb(local_card, "💻  Local AI (Ollama / LM Studio / llama.cpp)", sz=12, bold=True, col=TXT).pack(anchor="w", padx=14, pady=(10, 4))
    lb(local_card, "IA local con endpoint compatible con OpenAI. Sin depender de la nube.",
        sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 4))

    ep_row = ctk.CTkFrame(local_card, fg_color="transparent")
    ep_row.pack(fill="x", padx=14, pady=(2, 2))
    ep_row.grid_columnconfigure(1, weight=1)
    lb(ep_row, "Endpoint URL:", sz=10, col=MUT).grid(row=0, column=0, sticky="w")
    self.local_endpoint_entry = ctk.CTkEntry(ep_row, placeholder_text="http://localhost:11434/v1",
                                              font=("Consolas", 11), fg_color=CARD, text_color=TXT, border_color=BORD)
    self.local_endpoint_entry.grid(row=0, column=1, sticky="ew", padx=(6, 0))
    ep_val = config.get("LOCAL_AI_ENDPOINT", "")
    if ep_val:
        self.local_endpoint_entry.insert(0, ep_val)

    md_row = ctk.CTkFrame(local_card, fg_color="transparent")
    md_row.pack(fill="x", padx=14, pady=(2, 2))
    md_row.grid_columnconfigure(1, weight=1)
    lb(md_row, "Modelo:", sz=10, col=MUT).grid(row=0, column=0, sticky="w")
    self.local_model_entry = ctk.CTkEntry(md_row, placeholder_text="llama3.2, mistral, qwen2.5, ...",
                                           font=("Consolas", 11), fg_color=CARD, text_color=TXT, border_color=BORD)
    self.local_model_entry.grid(row=0, column=1, sticky="ew", padx=(6, 0))
    md_val = config.get("LOCAL_AI_MODEL", "llama3.2")
    self.local_model_entry.insert(0, md_val)

    ak_row = ctk.CTkFrame(local_card, fg_color="transparent")
    ak_row.pack(fill="x", padx=14, pady=(2, 2))
    ak_row.grid_columnconfigure(1, weight=1)
    lb(ak_row, "API Key (opcional):", sz=10, col=MUT).grid(row=0, column=0, sticky="w")
    self.local_key_entry = ctk.CTkEntry(ak_row, placeholder_text="sk-... (dejar vacío si no requiere)",
                                         font=("Consolas", 11), show="*", fg_color=CARD, text_color=TXT, border_color=BORD)
    self.local_key_entry.grid(row=0, column=1, sticky="ew", padx=(6, 0))
    lk_val = config.get("LOCAL_AI_API_KEY", "")
    if lk_val:
        self.local_key_entry.insert(0, lk_val)

    def guardar_local_ai():
        endpoint = self.local_endpoint_entry.get().strip()
        model = self.local_model_entry.get().strip()
        api_key = self.local_key_entry.get().strip()
        if not endpoint:
            self.log("❌  Ingresa la URL del endpoint local")
            return
        if not model:
            self.log("❌  Ingresa el nombre del modelo")
            return
        from src.core.config import load_config, save_config
        cfg = load_config()
        cfg["LOCAL_AI_ENDPOINT"] = endpoint
        cfg["LOCAL_AI_MODEL"] = model
        if api_key:
            cfg["LOCAL_AI_API_KEY"] = api_key
        else:
            if "LOCAL_AI_API_KEY" in cfg:
                del cfg["LOCAL_AI_API_KEY"]
        save_config(cfg)
        self.log(f"✅  Local AI guardado: {endpoint} | {model}")

    def test_local_ai():
        endpoint = self.local_endpoint_entry.get().strip()
        model = self.local_model_entry.get().strip()
        api_key = self.local_key_entry.get().strip()
        if not endpoint or not model:
            self.log("❌  Configura endpoint y modelo primero")
            return
        try:
            url = endpoint.rstrip("/") + "/chat/completions"
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Hola, respondeme solo OK."}],
                "max_tokens": 10,
            }
            r = requests.post(url, json=payload, headers=headers, timeout=10)
            resp = r.json()["choices"][0]["message"]["content"].strip()
            self.log(f"✅  Local AI responde ({r.status_code}): {resp}")
        except requests.exceptions.ConnectionError:
            self.log(f"❌  No se puede conectar a {endpoint}")
        except (KeyError, IndexError) as e:
            self.log(f"❌  Respuesta inesperada: {e}")
        except Exception as e:
            self.log(f"❌  Error: {e}")

    local_bf = ctk.CTkFrame(local_card, fg_color="transparent")
    local_bf.pack(fill="x", padx=14, pady=(4, 4))
    local_bf.grid_columnconfigure((0, 1, 2), weight=1)
    ctk.CTkButton(local_bf, text="👁", fg_color=CARD2, text_color=TXT,
                  command=lambda: toggle_key(self.local_key_entry),
                  height=30, corner_radius=8, width=40).grid(row=0, column=0, padx=(0, 4))
    ctk.CTkButton(local_bf, text="💾 Guardar", fg_color=GRN, text_color=GRN_T,
                  command=guardar_local_ai,
                  height=30, corner_radius=8, hover_color="#10b981").grid(row=0, column=1, padx=2)
    ctk.CTkButton(local_bf, text="🧪 Test", fg_color=PURP, text_color="#f3e8ff",
                  command=test_local_ai,
                  height=30, corner_radius=8).grid(row=0, column=2, padx=(4, 0))

    lk_stored = config.get("LOCAL_AI_API_KEY", "")
    ep_stored = config.get("LOCAL_AI_ENDPOINT", "")
    md_stored = config.get("LOCAL_AI_MODEL", "")
    if ep_stored or md_stored:
        lb(local_card, f"✅ Configurado: {ep_stored} | {md_stored}", sz=10, col=GRN_T).pack(anchor="w", padx=14, pady=(0, 8))
    else:
        lb(local_card, "❌ No configurado", sz=10, col=RED_T).pack(anchor="w", padx=14, pady=(0, 8))

    return tab
