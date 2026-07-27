import requests
from src.core.secrets_manager import load_config


def _headers():
    cfg = load_config()
    token = cfg.get("TWITCH_TOKEN", "").strip()
    client_id = cfg.get("TWITCH_CLIENT_ID", "").strip()
    if not token or not client_id:
        return None
    return {"Authorization": f"Bearer {token}", "Client-Id": client_id}


def _get_broadcaster_id():
    cfg = load_config()
    channel = cfg.get("CHANNEL", "").strip()
    h = _headers()
    if not h or not channel:
        return None
    try:
        r = requests.get(
            f"https://api.twitch.tv/helix/users?login={channel}",
            headers=h, timeout=10
        )
        data = r.json().get("data", [])
        return data[0]["id"] if data else None
    except Exception:
        return None


def create_clip():
    bid = _get_broadcaster_id()
    h = _headers()
    if not bid or not h:
        return "❌  No conectado a Twitch"
    try:
        r = requests.post(
            "https://api.twitch.tv/helix/clips",
            headers=h, params={"broadcaster_id": bid}, timeout=10
        )
        data = r.json().get("data", [])
        if data:
            url = data[0].get("edit_url", "")
            return f"✅  Clip creado: {url}"
        return "❌  No se pudo crear clip"
    except Exception as e:
        return f"❌  Error: {e}"


def create_marker(description=""):
    bid = _get_broadcaster_id()
    h = _headers()
    if not bid or not h:
        return "❌  No conectado a Twitch"
    try:
        body = {"user_id": bid}
        if description:
            body["description"] = description
        r = requests.post(
            "https://api.twitch.tv/helix/streams/markers",
            headers=h, json=body, timeout=10
        )
        data = r.json().get("data", [])
        if data:
            return f"📍  Marcador creado: {data[0].get('description', '') or 'sin descripcion'}"
        return "❌  No se pudo crear marcador (¿el stream está en vivo?)"
    except Exception as e:
        return f"❌  Error: {e}"


def get_stream_info():
    cfg = load_config()
    channel = cfg.get("CHANNEL", "").strip()
    h = _headers()
    if not h or not channel:
        return None
    try:
        r = requests.get(
            f"https://api.twitch.tv/helix/streams?user_login={channel}",
            headers=h, timeout=10
        )
        data = r.json().get("data", [])
        if data:
            return {
                "title": data[0].get("title", ""),
                "game": data[0].get("game_name", ""),
                "viewers": data[0].get("viewer_count", 0),
                "started_at": data[0].get("started_at", ""),
            }
        return {"title": "Offline", "game": "Offline", "viewers": 0, "started_at": ""}
    except Exception:
        return None


def set_stream_info(title=None, game_id=None):
    bid = _get_broadcaster_id()
    h = _headers()
    if not bid or not h:
        return "❌  No conectado a Twitch"
    try:
        body = {}
        if title is not None:
            body["title"] = title
        if game_id is not None:
            body["game_id"] = game_id
        r = requests.patch(
            f"https://api.twitch.tv/helix/channels?broadcaster_id={bid}",
            headers=h, json=body, timeout=10
        )
        if r.status_code in (200, 204):
            return "✅  Información actualizada"
        return f"❌  Error {r.status_code}: {r.text}"
    except Exception as e:
        return f"❌  Error: {e}"


def search_games(query):
    h = _headers()
    if not h:
        return []
    try:
        r = requests.get(
            "https://api.twitch.tv/helix/games",
            headers=h, params={"name": query}, timeout=10
        )
        return [(g["id"], g["name"]) for g in r.json().get("data", [])]
    except Exception:
        return []
