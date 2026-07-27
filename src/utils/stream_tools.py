"""Stream tools — quotes, raffle, game queue, schedule, user notes, keyword alerts, link blocking, song requests."""
import os, json, random, re, threading, time
from src import PROJECT_ROOT
from src.utils.log import error

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ─── Helpers ────────────────────────────────────────────────────────────────

def _load(name, default=None):
    path = os.path.join(DATA_DIR, name)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default if default is not None else {}
    return default if default is not None else {}

def _save(name, data):
    path = os.path.join(DATA_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ─── 1. Quotes ──────────────────────────────────────────────────────────────

def quote_add(text, author):
    data = _load("quotes.json", [])
    data.append({"id": len(data) + 1, "text": text, "author": author, "time": time.time()})
    _save("quotes.json", data)
    return data[-1]["id"]

def quote_get(qid=None):
    data = _load("quotes.json", [])
    if not data:
        return None
    if qid is not None:
        for q in data:
            if q["id"] == qid:
                return q
        return None
    return random.choice(data)

def quote_remove(qid):
    data = _load("quotes.json", [])
    data = [q for q in data if q["id"] != qid]
    _save("quotes.json", data)

def quote_count():
    return len(_load("quotes.json", []))

# ─── 2. Raffle ──────────────────────────────────────────────────────────────

def raffle_open():
    data = _load("raffle.json", {"active": False, "entries": []})
    data["active"] = True
    data["entries"] = []
    _save("raffle.json", data)

def raffle_close():
    data = _load("raffle.json", {"active": False, "entries": []})
    data["active"] = False
    _save("raffle.json", data)

def raffle_enter(user):
    data = _load("raffle.json", {"active": False, "entries": []})
    if not data.get("active"):
        return False, "No hay sorteo activo"
    if any(e["user"].lower() == user.lower() for e in data["entries"]):
        return False, "Ya estás participando"
    data["entries"].append({"user": user, "time": time.time()})
    _save("raffle.json", data)
    return True, f"{user} agregado al sorteo"

def raffle_pick():
    data = _load("raffle.json", {"active": False, "entries": []})
    if not data.get("entries"):
        return None, "No hay participantes"
    winner = random.choice(data["entries"])
    data["active"] = False
    _save("raffle.json", data)
    return winner["user"], f"🎉 Ganador: {winner['user']}"

def raffle_count():
    data = _load("raffle.json", {"active": False, "entries": []})
    return len(data.get("entries", []))

def raffle_is_active():
    return _load("raffle.json", {"active": False}).get("active", False)

# ─── 3. Game Queue ──────────────────────────────────────────────────────────

def gqueue_join(user):
    data = _load("game_queue.json", {"queue": []})
    if any(u.lower() == user.lower() for u in data["queue"]):
        return False, "Ya estás en la cola"
    data["queue"].append(user)
    _save("game_queue.json", data)
    return True, f"{user} agregado a la cola"

def gqueue_leave(user):
    data = _load("game_queue.json", {"queue": []})
    data["queue"] = [u for u in data["queue"] if u.lower() != user.lower()]
    _save("game_queue.json", data)
    return True, f"{user} eliminado de la cola"

def gqueue_pick():
    data = _load("game_queue.json", {"queue": []})
    if not data["queue"]:
        return None, "La cola está vacía"
    pick = random.choice(data["queue"])
    data["queue"] = [u for u in data["queue"] if u.lower() != pick.lower()]
    _save("game_queue.json", data)
    return pick, f"🎮 Siguiente: {pick}"

def gqueue_list():
    data = _load("game_queue.json", {"queue": []})
    return data["queue"]

# ─── 4. Schedule ────────────────────────────────────────────────────────────

DAYS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]

def schedule_set(day, text):
    data = _load("schedule.json", {})
    data[day.lower()] = text
    _save("schedule.json", data)

def schedule_get(day=None):
    data = _load("schedule.json", {})
    if day:
        return data.get(day.lower(), "")
    return data

def schedule_format():
    data = _load("schedule.json", {})
    if not data:
        return "No hay horario configurado"
    lines = ["📅  Horario de streams:"]
    for d in DAYS:
        if d in data:
            lines.append(f"  {d.capitalize()}: {data[d]}")
    return "\n".join(lines) if len(lines) > 1 else "No hay horario configurado"

# ─── 5. User Notes ─────────────────────────────────────────────────────────

def note_set(user, text):
    data = _load("notes.json", {})
    if user not in data:
        data[user] = []
    data[user].append({"text": text, "time": time.time()})
    _save("notes.json", data)

def note_get(user):
    data = _load("notes.json", {})
    return data.get(user, [])

def note_remove(user, idx):
    data = _load("notes.json", {})
    if user in data and 0 <= idx < len(data[user]):
        data[user].pop(idx)
        if not data[user]:
            del data[user]
        _save("notes.json", data)
        return True
    return False

# ─── 6. Keyword Alerts ─────────────────────────────────────────────────────

def keyword_add(keyword, response):
    data = _load("keyword_alerts.json", {})
    data[keyword.lower()] = response
    _save("keyword_alerts.json", data)

def keyword_remove(keyword):
    data = _load("keyword_alerts.json", {})
    data.pop(keyword.lower(), None)
    _save("keyword_alerts.json", data)

def keyword_check(text):
    data = _load("keyword_alerts.json", {})
    text_lower = text.lower()
    for kw, resp in data.items():
        if kw in text_lower:
            return resp
    return None

def keyword_list():
    return _load("keyword_alerts.json", {})

# ─── 7. Link Blocking ──────────────────────────────────────────────────────

def linkblock_check(text, whitelist=None):
    url_pattern = re.compile(r'https?://[^\s]+|www\.[^\s]+', re.IGNORECASE)
    urls = url_pattern.findall(text)
    if not urls:
        return None
    if whitelist:
        for url in urls:
            allowed = False
            for domain in whitelist:
                if domain.lower() in url.lower():
                    allowed = True
                    break
            if not allowed:
                return url
        return None
    return urls[0] if urls else None

def linkblock_set_whitelist(domains):
    data = _load("linkblock.json", {"whitelist": [], "action": "log"})
    data["whitelist"] = domains
    _save("linkblock.json", data)

def linkblock_get_whitelist():
    return _load("linkblock.json", {"whitelist": []}).get("whitelist", [])

def linkblock_set_action(action):
    data = _load("linkblock.json", {"whitelist": [], "action": "log"})
    data["action"] = action
    _save("linkblock.json", data)

def linkblock_get_action():
    return _load("linkblock.json", {"whitelist": [], "action": "log"}).get("action", "log")

# ─── 8. Song Requests ──────────────────────────────────────────────────────

def songreq_enqueue(url, user):
    data = _load("song_queue.json", {"queue": []})
    data["queue"].append({"url": url, "user": user, "time": time.time()})
    _save("song_queue.json", data)
    return len(data["queue"])

def songreq_dequeue():
    data = _load("song_queue.json", {"queue": []})
    if not data["queue"]:
        return None
    song = data["queue"].pop(0)
    _save("song_queue.json", data)
    return song

def songreq_list():
    return _load("song_queue.json", {"queue": []}).get("queue", [])

def songreq_clear():
    _save("song_queue.json", {"queue": []})

def songreq_download(url, output_dir=None):
    """Download audio from URL using yt-dlp. Returns path or None."""
    if output_dir is None:
        output_dir = os.path.join(PROJECT_ROOT, "data", "songs")
    os.makedirs(output_dir, exist_ok=True)
    try:
        import yt_dlp
        out_template = os.path.join(output_dir, "%(title)s.%(ext)s")
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": out_template,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }],
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "audio")
            return os.path.join(output_dir, f"{title}.wav")
    except ImportError:
        return None
    except Exception:
        return None

def songreq_play(path, device=None):
    """Play an audio file (async)."""
    if not path or not os.path.exists(path):
        return False
    try:
        from src.audio import play_file
        threading.Thread(target=play_file, args=(path, device), daemon=True).start()
        return True
    except Exception:
        return False

# ─── 9. Auto-shoutout ──────────────────────────────────────────────────────

def soset_enabled(val):
    data = _load("shoutout.json", {"enabled": True})
    data["enabled"] = val
    _save("shoutout.json", data)

def so_is_enabled():
    return _load("shoutout.json", {"enabled": True}).get("enabled", True)
