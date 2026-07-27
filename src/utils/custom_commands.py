import os, json, re, random
from src import PROJECT_ROOT
from src.utils.log import error

CMDS_FILE = os.path.join(PROJECT_ROOT, "data", "comandos_personalizados.json")


def _load():
    if os.path.exists(CMDS_FILE):
        try:
            with open(CMDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save(commands):
    os.makedirs(os.path.dirname(CMDS_FILE), exist_ok=True)
    with open(CMDS_FILE, "w", encoding="utf-8") as f:
        json.dump(commands, f, indent=2, ensure_ascii=False)


def get_commands():
    return _load()


def set_command(name, response):
    cmds = _load()
    cmds[name.lower()] = response
    _save(cmds)


def remove_command(name):
    cmds = _load()
    cmds.pop(name.lower(), None)
    _save(cmds)


def placeholder_vars(channel=None, user=None, stream_title=None, stream_game=None):
    return {
        "{channel.name}": channel or "channel",
        "{user}": user or "user",
        "{stream.title}": stream_title or "stream title",
        "{stream.game}": stream_game or "game",
        "{my.name}": "Karin",
        "{rand}": str(random.randint(1, 100)),
    }


def resolve(text, args=None, extra_vars=None):
    if not text:
        return text
    vars_map = dict(extra_vars or {})
    if args:
        for i, arg in enumerate(args, 1):
            vars_map[f"{{{i}}}"] = arg
    for key, val in vars_map.items():
        text = text.replace(key, val)
    return text


def execute(name, args=None, channel=None, user=None, stream_title=None, stream_game=None):
    cmds = _load()
    entry = cmds.get(name.lower())
    if not entry:
        return None
    response = entry if isinstance(entry, str) else entry.get("response", "")
    if not response:
        return None
    extra = placeholder_vars(channel, user, stream_title, stream_game)
    return resolve(response, args, extra)
