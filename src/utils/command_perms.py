import os, json
from src import PROJECT_ROOT

DATA_FILE = os.path.join(PROJECT_ROOT, "data", "permisos_comandos.json")
DEFAULT_PERM = "everyone"

LEVELS = ["admin", "mod", "sub", "follow", "everyone"]
LEVEL_LABELS = {
    "admin": "🔴 Solo streamer",
    "mod": "🛡 Moderadores+",
    "sub": "🌟 Subscriptores+",
    "follow": "❤️ Seguidores+",
    "everyone": "👥 Todos",
}


def _load():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"default": DEFAULT_PERM, "commands": {}}
    return {"default": DEFAULT_PERM, "commands": {}}


def _save(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_permission(command):
    data = _load()
    cmd = command.lower().lstrip("!")
    return data["commands"].get(cmd, data.get("default", DEFAULT_PERM))


def set_permission(command, level):
    data = _load()
    cmd = command.lower().lstrip("!")
    data["commands"][cmd] = level
    _save(data)


def remove_permission(command):
    data = _load()
    cmd = command.lower().lstrip("!")
    data["commands"].pop(cmd, None)
    _save(data)


def get_default():
    return _load().get("default", DEFAULT_PERM)


def set_default(level):
    data = _load()
    data["default"] = level
    _save(data)


def get_all_permissions():
    data = _load()
    return data.get("commands", {})


def get_commands_list():
    """Returns dict of command -> permission level (including default fallback)."""
    data = _load()
    default = data.get("default", DEFAULT_PERM)
    cmds = {}
    for cmd, level in data.get("commands", {}).items():
        cmds[cmd] = level
    return cmds, default


def check_role(message):
    """Returns the highest role for a user: admin, mod, sub, follow, or everyone."""
    author = message.author
    if getattr(author, "is_broadcaster", False):
        return "admin"
    if getattr(author, "is_mod", False):
        return "mod"
    if getattr(author, "is_subscriber", False):
        return "sub"
    return "everyone"


def check_follower(user_id, broadcaster_id, token, client_id):
    """Check if a user follows the channel."""
    if not user_id or not broadcaster_id:
        return False
    try:
        import requests
        r = requests.get(
            f"https://api.twitch.tv/helix/channels/followers",
            params={"broadcaster_id": broadcaster_id, "user_id": user_id},
            headers={"Authorization": f"Bearer {token}", "Client-Id": client_id},
            timeout=5,
        )
        data = r.json()
        return len(data.get("data", [])) > 0
    except Exception:
        return False


def get_user_id(username, token, client_id):
    """Resolve a Twitch username to user ID."""
    try:
        import requests
        r = requests.get(
            f"https://api.twitch.tv/helix/users?login={username}",
            headers={"Authorization": f"Bearer {token}", "Client-Id": client_id},
            timeout=5,
        )
        data = r.json().get("data", [])
        return data[0]["id"] if data else None
    except Exception:
        return None


def has_permission(command, user_role, message=None, token=None, client_id=None, broadcaster_id=None):
    """Check if user_role meets the required level for a command."""
    required = get_permission(command)
    levels = ["everyone", "follow", "sub", "mod", "admin"]
    user_idx = levels.index(user_role) if user_role in levels else 0
    req_idx = levels.index(required) if required in levels else 0

    if user_idx >= req_idx:
        return True

    # Special case: if user is "everyone" but we need "follow", check API
    if required == "follow" and user_role == "everyone" and message and token and client_id and broadcaster_id:
        user_id = get_user_id(message.author.name, token, client_id)
        if user_id:
            return check_follower(user_id, broadcaster_id, token, client_id)

    return False
