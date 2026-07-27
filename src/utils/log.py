import sys, os, time
from src import PROJECT_ROOT as _ROOT

LEVELS = {"DEBUG": 0, "INFO": 1, "WARN": 2, "ERROR": 3}
_LEVEL = "DEBUG"
_LOG_DIR = os.path.join(_ROOT, "logs")
_LOG_FILE = None
_LOG_FH = None


def set_level(name):
    global _LEVEL
    if name in LEVELS:
        _LEVEL = name


def _ensure_logfile():
    global _LOG_FILE, _LOG_FH
    try:
        os.makedirs(_LOG_DIR, exist_ok=True)
        today = time.strftime("%Y-%m-%d")
        path = os.path.join(_LOG_DIR, f"karin-{today}.log")
        if path != _LOG_FILE:
            if _LOG_FH:
                try:
                    _LOG_FH.close()
                except Exception:
                    pass
            _LOG_FILE = path
            _LOG_FH = open(path, "a", encoding="utf-8")
    except Exception:
        pass


def _fmt(level, msg):
    ts = time.strftime("%H:%M:%S")
    return f"[{ts}][{level:<5}] {msg}"


def _write(level, msg):
    line = _fmt(level, msg)
    if level == "ERROR":
        print(line, file=sys.stderr)
    else:
        print(line)
    _ensure_logfile()
    if _LOG_FH:
        try:
            _LOG_FH.write(f"[{time.strftime('%Y-%m-%d')}] {line}\n")
            _LOG_FH.flush()
        except Exception:
            pass


def debug(msg):
    if LEVELS.get(_LEVEL, 0) <= 0:
        _write("DEBUG", msg)


def info(msg):
    if LEVELS.get(_LEVEL, 0) <= 1:
        _write("INFO", msg)


def warn(msg):
    if LEVELS.get(_LEVEL, 0) <= 2:
        _write("WARN", msg)


def error(msg):
    if LEVELS.get(_LEVEL, 0) <= 3:
        _write("ERROR", msg)
