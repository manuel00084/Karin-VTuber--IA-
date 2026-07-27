from .ptt import PTTManager

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False


def get_game_watcher():
    from .game_watcher import GameWatcher
    return GameWatcher