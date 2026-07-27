import re, requests, time
from plugins import PluginManager

# ── Emotion tag ──
_EMO_RE = re.compile(r'^\[(alegre|triste|enojado|sorpresa|neutro)\]\s*')
_EMO_MAP = {
    "alegre": "feliz", "triste": "triste",
    "enojado": "enojado", "sorpresa": "sorpresa",
    "neutro": "neutro",
}

# ── Auto-discovery cache ──
_models_cache = {}
_CACHE_TTL = 3600

_VISION_KEYWORDS = {"llama-4-scout", "llama-4-maverick", "llama-4"}

# ── Fallback entre proveedores ──
_PROVIDER_API_KEY_MAP = {
    "groq": "GROQ_API_KEY",
    "cerebras": "CEREBRAS_API_KEY",
    "google_studio": "GOOGLE_STUDIO_API_KEY",
    "local": "LOCAL_AI_API_KEY",
}
_PROVIDER_FALLBACK = {
    "groq": ["cerebras", "google_studio"],
    "cerebras": ["groq", "google_studio"],
    "google_studio": ["groq", "cerebras"],
    "local": [],
}


def _fetch_provider_models(provider, api_key):
    models_urls = {
        "groq": "https://api.groq.com/openai/v1/models",
        "cerebras": "https://api.cerebras.ai/v1/models",
    }
    url = models_urls.get(provider)
    if not url or not api_key:
        return None
    try:
        headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json().get("data", [])
        texto, vision = [], []
        for m in data:
            mid = m.get("id", "")
            if not m.get("active", True) or not mid:
                continue
            if any(x in mid for x in ["embedding", "whisper", "tts", "stt"]):
                continue
            if any(vp in mid for vp in _VISION_KEYWORDS):
                vision.append(mid)
            else:
                texto.append(mid)

        def _sort_key(name):
            for p, s in [("235b", 5), ("120b", 5), ("70b", 4), ("32b", 3), ("9b", 2), ("8b", 1)]:
                if p in name.lower():
                    return -s
            return 0

        texto.sort(key=_sort_key)
        vision.sort(key=_sort_key)
        return {"texto": texto, "vision": vision}
    except Exception:
        return None


def _get_models(provider, api_key, vision=False):
    now = time.time()
    cached = _models_cache.get(provider)
    if cached and (now - cached["timestamp"]) < _CACHE_TTL:
        return cached["vision"] if vision else cached["texto"]
    fetched = _fetch_provider_models(provider, api_key)
    if fetched:
        _models_cache[provider] = {**fetched, "timestamp": now}
        return fetched["vision"] if vision else fetched["texto"]
    cfg = PROVIDERS.get(provider, PROVIDERS["groq"])
    return cfg.get("models_vision", []) if vision and cfg.get("models_vision") else cfg["models_texto"]


PROVIDERS = {
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "models_texto": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "deepseek-r1-distill-llama-70b",
            "gemma2-9b-it",
        ],
        "models_vision": [
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
        ],
    },
    "cerebras": {
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "models_texto": ["gpt-oss-120b"],
        "models_vision": [],
    },
    "google_studio": {
        "url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        "models_texto": ["gemini-2.0-flash", "gemini-2.0-flash-001", "gemini-2.5-flash"],
        "models_vision": ["gemini-2.0-flash", "gemini-2.0-flash-001", "gemini-2.5-flash"],
    },
    "local": {
        "url": "",  # taken from LOCAL_AI_ENDPOINT config
        "models_texto": [],
        "models_vision": [],
    },
}


def ask_ai(text, api_key, prompt, provider="groq", max_caracteres=500, reintentos=3, vision=False):
    """
    Envía un mensaje a un proveedor de IA y devuelve la respuesta.
    Si el proveedor falla por rate-limit, prueba los proveedores
    de respaldo definidos en _PROVIDER_FALLBACK.
    """
    if not text or text.strip() == "":
        return "⚠ El mensaje está vacío"

    providers_try = [provider] + _PROVIDER_FALLBACK.get(provider, [])
    providers_tried = set()
    seen_msgs = set()

    for prov in providers_try:
        if prov in providers_tried:
            continue
        providers_tried.add(prov)

        # Resolver API key para este proveedor
        if prov == "local":
            prov_key = None
        elif prov == provider:
            prov_key = api_key
        else:
            from src.core.config import load_config
            cfg = load_config()
            key_name = _PROVIDER_API_KEY_MAP.get(prov)
            prov_key = cfg.get(key_name, "") if key_name else ""

        if prov != "local" and (not prov_key or prov_key.strip() == ""):
            continue

        headers = {
            "Authorization": f"Bearer {prov_key.strip()}",
            "Content-Type": "application/json"
        }

        prompt_limitado = (
            f"{prompt}\n\n"
            "Es, max400, sin md.\n"
            "Antepón [alegre][triste][enojado][sorpresa][neutro]. Ej: [alegre] ok"
        )

        cfg = PROVIDERS.get(prov)
        if not cfg:
            cfg = PROVIDERS.get("groq")

        if prov == "local":
            try:
                from src.core.config import load_config as _lc
                lcfg = _lc()
                url = lcfg.get("LOCAL_AI_ENDPOINT", "http://localhost:11434/v1").rstrip("/") + "/chat/completions"
                modelo = lcfg.get("LOCAL_AI_MODEL", "llama3.2")
                modelos = [modelo]
            except Exception:
                continue
        else:
            url = cfg["url"]
            modelos = _get_models(prov, prov_key, vision=vision)
            if not modelos:
                modelos = PROVIDERS["groq"]["models_vision"] if vision else PROVIDERS["groq"]["models_texto"]

        for modelo in modelos:
            for intento in range(reintentos):
                try:
                    if prov == "google_studio":
                        req_url = url.format(model=modelo) + f"?key={prov_key.strip()}"
                        req_headers = {"Content-Type": "application/json"}
                        req_data = {
                            "contents": [{
                                "parts": [{"text": f"{prompt_limitado}\n\n{text}"}]
                            }],
                            "generationConfig": {
                                "maxOutputTokens": 700 if vision else 200,
                                "temperature": 0.05 if vision else 0.5,
                            }
                        }
                    else:
                        req_url = url
                        req_headers = headers
                        req_data = {
                            "messages": [
                                {"role": "system", "content": prompt_limitado},
                                {"role": "user",   "content": text}
                            ],
                            "model":       modelo,
                            "max_tokens":  700 if vision else 200,
                            "temperature": 0.05 if vision else 0.5,
                        }
                    r = requests.post(req_url, json=req_data, headers=req_headers, timeout=30)
                    if r.status_code == 429:
                        # Rate limit — probar siguiente proveedor o reintentar
                        if intento < reintentos - 1:
                            time.sleep(2 ** intento)
                            continue
                        break  # sale del modelo loop, prueba otro proveedor
                    if r.status_code == 503:
                        time.sleep(1)
                        break
                    if r.status_code == 401:
                        msg = "⚠ API Key inválida"
                        if msg not in seen_msgs:
                            seen_msgs.add(msg)
                        break
                    if r.status_code in (400, 404):
                        break
                    if r.status_code != 200:
                        time.sleep(1)
                        continue
                    if prov == "google_studio":
                        respuesta = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    else:
                        respuesta = r.json()["choices"][0]["message"]["content"].strip()
                    # Strip emotion tag
                    emo_match = _EMO_RE.match(respuesta)
                    emotion = emo_match.group(1) if emo_match else "neutro"
                    if emo_match:
                        respuesta = respuesta[emo_match.end():]
                    for char in ["*", "#", "`", "_"]:
                        respuesta = respuesta.replace(char, "")
                    if len(respuesta) > max_caracteres:
                        respuesta = respuesta[:max_caracteres].rsplit(" ", 1)[0] + "..."
                    texto_final = respuesta if respuesta else "Hmm, no supe qué decir..."
                    PluginManager().emit("ai_response", texto_final)
                    PluginManager().emit("ai_emotion", _EMO_MAP.get(emotion, "neutro"))
                    return texto_final
                except requests.exceptions.Timeout:
                    time.sleep(0.5)
                    continue
                except requests.exceptions.ConnectionError:
                    continue
                except (KeyError, IndexError):
                    time.sleep(1)
                    continue
                except Exception:
                    time.sleep(0.5)
                    continue
    return "⚠ El servicio no está respondiendo. Intenta más tarde."


def ask_vision(image_b64, texto, api_key, prompt="", modelo_idx=0, provider="groq", log=print):
    """Traduce/detecta texto en imagen usando IA con visión."""
    cfg = PROVIDERS.get(provider)
    if not cfg:
        cfg = PROVIDERS.get("groq")

    if provider == "local":
        try:
            from src.core.config import load_config
            lcfg = load_config()
            url = lcfg.get("LOCAL_AI_ENDPOINT", "http://localhost:11434/v1").rstrip("/") + "/chat/completions"
            modelo = lcfg.get("LOCAL_AI_MODEL", "llama3.2")
            modelos = [modelo]
        except Exception:
            if log:
                log("⚠ Error leyendo configuración local")
            return None, modelo_idx, False
    else:
        modelos = _get_models(provider, api_key, vision=True)
    if not modelos:
        if log:
            log(f"⚠ '{provider}' no tiene modelos de visión disponibles")
        return None, modelo_idx, False
    
    for idx, modelo in enumerate(modelos):
        for intento in range(2):
            try:
                if provider == "google_studio":
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key.strip()}"
                    headers = {"Content-Type": "application/json"}
                    data = {
                        "contents": [{
                            "parts": [
                                {"text": prompt + "\n\n" + texto},
                                {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}}
                            ]
                        }]
                    }
                else:
                    url = cfg["url"]
                    headers = {
                        "Authorization": f"Bearer {api_key.strip()}",
                        "Content-Type": "application/json"
                    }
                    data = {
                        "model": modelo,
                        "messages": [
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": [
                                {"type": "image_url",
                                 "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                                {"type": "text", "text": texto}
                            ]}
                        ],
                        "max_tokens": 700,
                        "temperature": 0.05,
                    }
                
                r = requests.post(url, json=data, headers=headers, timeout=30)
                if r.status_code == 429:
                    espera = 2 ** (intento + 2)  # 4s, 8s
                    time.sleep(espera)
                    continue
                if r.status_code in (400, 404):
                    if log:
                        try:
                            detalle = r.json().get("error", {}).get("message", r.text[:200])
                        except Exception:
                            detalle = r.text[:200]
                        log(f"⚠ API 400 con {provider}/{modelo}: {detalle}")
                    break  # next model
                if r.status_code in (401, 403):
                    return None, idx, False
                if r.status_code != 200:
                    time.sleep(0.5)
                    continue
                
                if provider == "google_studio":
                    respuesta = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                else:
                    respuesta = r.json()["choices"][0]["message"]["content"].strip()
                
                for char in ["*", "#", "`", "_"]:
                    respuesta = respuesta.replace(char, "")
                return respuesta, idx, False
            except requests.exceptions.Timeout:
                time.sleep(0.5)
                continue
            except requests.exceptions.ConnectionError:
                return None, idx, False
            except (KeyError, IndexError):
                time.sleep(0.5)
                continue
            except Exception:
                time.sleep(0.5)
                continue
    return None, len(modelos) - 1, False