"""
Music Player Plugin — controla Spotify desde Twitch chat.
Comandos: !play <canción>, !skip, !np, !pause, !resume, !queue
Requiere spotipy: pip install spotipy
"""
import threading
import customtkinter as ctk

api = None
_spotify = None
_np_cache = {"track": "", "artist": "", "album": "", "duration": 0, "progress": 0}


def _init_spotify():
    global _spotify
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
    except ImportError:
        api.log("[Music] spotipy no instalado — corre: pip install spotipy")
        return False

    cid = api.get_config("SPOTIFY_CLIENT_ID", "")
    secret = api.get_config("SPOTIFY_CLIENT_SECRET", "")
    redirect = api.get_config("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")

    if not cid or not secret:
        api.log("[Music] Falta SPOTIFY_CLIENT_ID o SPOTIFY_CLIENT_SECRET en config")
        api.log("[Music] Créalos en https://developer.spotify.com/dashboard")
        return False

    try:
        _spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=cid, client_secret=secret,
            redirect_uri=redirect,
            scope="user-read-playback-state user-modify-playback-state user-read-currently-playing"
        ))
        api.log("[Music] ✅ Conectado a Spotify")
        return True
    except Exception as e:
        api.log(f"[Music] Error conectando Spotify: {e}")
        return False


def on_load(_api):
    global api
    api = _api
    api.log("[Music] Cargando Music Player...")
    threading.Thread(target=_init_spotify, daemon=True).start()
    api.register_command("play", _cmd_play)
    api.register_command("skip", _cmd_skip)
    api.register_command("np", _cmd_np)
    api.register_command("pause", _cmd_pause)
    api.register_command("resume", _cmd_resume)
    api.log("[Music] Comandos registrados: !play, !skip, !np, !pause, !resume")
    return True


def on_unload():
    api.log("[Music] Descargado.")


# ── Comandos Twitch ──────────────────────────────────────────

def _ensure_spotify():
    if _spotify is None:
        _init_spotify()
    return _spotify is not None


def _cmd_play(user, args):
    if not _ensure_spotify():
        return "Spotify no conectado. Configura SPOTIFY_CLIENT_ID"
    if not args:
        return "Uso: !play <canción>"
    try:
        results = _spotify.search(q=args, type="track", limit=1)
        items = results.get("tracks", {}).get("items", [])
        if not items:
            return f"No encontré '{args}'"
        track = items[0]
        uri = track["uri"]
        devices = _spotify.devices()
        if not devices.get("devices"):
            return "No hay dispositivo Spotify activo"
        dev_id = devices["devices"][0]["id"]
        _spotify.start_playback(device_id=dev_id, uris=[uri])
        return f"▶ {track['name']} — {track['artists'][0]['name']}"
    except Exception as e:
        api.log(f"[Music] !play error: {e}")
        return f"Error: {e}"


def _cmd_skip(user, args):
    if not _ensure_spotify():
        return "Spotify no conectado"
    try:
        _spotify.next_track()
        _update_np()
        return f"⏭  Siguiente: {_np_cache['track']} — {_np_cache['artist']}"
    except Exception as e:
        return f"Error: {e}"


def _cmd_np(user, args):
    _update_np()
    t = _np_cache["track"]
    if not t:
        return "No hay nada reproduciéndose"
    prog = _np_cache["progress"]
    dur = _np_cache["duration"]
    bar = _barra(prog, dur)
    return f"🎵 {t} — {_np_cache['artist']}  {bar}  {_fmt(prog)} / {_fmt(dur)}"


def _cmd_pause(user, args):
    if not _ensure_spotify():
        return "Spotify no conectado"
    try:
        _spotify.pause_playback()
        return "⏸  Pausado"
    except Exception as e:
        return f"Error: {e}"


def _cmd_resume(user, args):
    if not _ensure_spotify():
        return "Spotify no conectado"
    try:
        _spotify.start_playback()
        return "▶  Reanudado"
    except Exception as e:
        return f"Error: {e}"


# ── Helpers ──────────────────────────────────────────────────

def _update_np():
    global _np_cache
    if not _spotify:
        return
    try:
        cur = _spotify.current_playback()
        if cur and cur.get("item"):
            item = cur["item"]
            _np_cache["track"] = item["name"]
            _np_cache["artist"] = ", ".join(a["name"] for a in item["artists"])
            _np_cache["album"] = item["album"]["name"]
            _np_cache["duration"] = item["duration_ms"]
            _np_cache["progress"] = cur.get("progress_ms", 0)
    except Exception:
        pass


def _fmt(ms):
    s = ms // 1000
    m, s = divmod(s, 60)
    return f"{m}:{s:02d}"


def _barra(prog, dur):
    if not dur:
        return ""
    pct = prog / dur
    llenos = int(pct * 10)
    return "▰" * llenos + "▱" * (10 - llenos)


# ── UI Tab ───────────────────────────────────────────────────

def on_ui_tab(parent_frame):
    frame = ctk.CTkScrollableFrame(parent_frame, fg_color="transparent")

    ctk.CTkLabel(frame, text="🎵  Music Player", font=("Segoe UI", 18, "bold"),
                 text_color="#c084fc").pack(anchor="w", padx=20, pady=(20, 5))
    ctk.CTkLabel(frame, text="Controla Spotify desde Twitch chat", font=("Segoe UI", 11),
                 text_color="#94a3b8").pack(anchor="w", padx=20, pady=(0, 15))

    # Config section
    cfg_frame = ctk.CTkFrame(frame, fg_color="#1e1e2e", corner_radius=8)
    cfg_frame.pack(fill="x", padx=20, pady=5)

    ctk.CTkLabel(cfg_frame, text="Configuración Spotify", font=("Segoe UI", 12, "bold"),
                 text_color="#e2e8f0").pack(anchor="w", padx=14, pady=(10, 4))

    cid_var = ctk.StringVar(value=api.get_config("SPOTIFY_CLIENT_ID", ""))
    ctk.CTkLabel(cfg_frame, text="Client ID:", font=("Segoe UI", 11),
                 text_color="#94a3b8").pack(anchor="w", padx=14, pady=(4, 0))
    ctk.CTkEntry(cfg_frame, textvariable=cid_var, font=("Consolas", 11),
                 fg_color="#11111b", text_color="#e2e8f0", border_color="#313244"
                 ).pack(fill="x", padx=14, pady=(2, 6))

    sec_var = ctk.StringVar(value=api.get_config("SPOTIFY_CLIENT_SECRET", ""))
    ctk.CTkLabel(cfg_frame, text="Client Secret:", font=("Segoe UI", 11),
                 text_color="#94a3b8").pack(anchor="w", padx=14, pady=(4, 0))
    ctk.CTkEntry(cfg_frame, textvariable=sec_var, font=("Consolas", 11),
                 fg_color="#11111b", text_color="#e2e8f0", border_color="#313244",
                 show="*").pack(fill="x", padx=14, pady=(2, 6))

    def _guardar_spotify():
        api.set_config("SPOTIFY_CLIENT_ID", cid_var.get())
        api.set_config("SPOTIFY_CLIENT_SECRET", sec_var.get())
        api.log("[Music] Credenciales guardadas. Reconectando...")
        global _spotify
        _spotify = None
        threading.Thread(target=_init_spotify, daemon=True).start()

    ctk.CTkButton(cfg_frame, text="💾 Guardar y conectar",
                  fg_color="#7c3aed", hover_color="#6d28d9",
                  font=("Segoe UI", 11), height=28,
                  command=_guardar_spotify).pack(anchor="w", padx=14, pady=(4, 10))

    # Now Playing
    np_frame = ctk.CTkFrame(frame, fg_color="#1e1e2e", corner_radius=8)
    np_frame.pack(fill="x", padx=20, pady=10)
    np_label = ctk.CTkLabel(np_frame, text="🎶  Sin reproducción",
                            font=("Segoe UI", 13), text_color="#a1a1aa")
    np_label.pack(padx=14, pady=12)

    def _refresh_np():
        _update_np()
        t = _np_cache["track"]
        if t:
            np_label.configure(
                text=f"▶ {t}  —  {_np_cache['artist']}\n{_np_cache['album']}")
        frame.after(5000, _refresh_np)

    frame.after(1000, _refresh_np)

    return frame
