import subprocess, os, json, psutil, re, winreg
from src import PROJECT_ROOT


GAMES_FILE = os.path.join(PROJECT_ROOT, "data", "juegos_lanzador.json")


def _load():
    if os.path.exists(GAMES_FILE):
        try:
            with open(GAMES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save(games):
    os.makedirs(os.path.dirname(GAMES_FILE), exist_ok=True)
    with open(GAMES_FILE, "w", encoding="utf-8") as f:
        json.dump(games, f, indent=2, ensure_ascii=False)


def get_games():
    return _load()


def add_game(name, exe_path, args=""):
    games = _load()
    for g in games:
        if g["name"].lower() == name.lower():
            g["exe_path"] = exe_path
            g["args"] = args
            _save(games)
            return True
    games.append({"name": name, "exe_path": exe_path, "args": args})
    _save(games)
    return True


def remove_game(name):
    games = _load()
    games = [g for g in games if g["name"].lower() != name.lower()]
    _save(games)


def open_game(name):
    games = _load()
    for g in games:
        if g["name"].lower() == name.lower():
            exe = g["exe_path"]
            args = g.get("args", "")
            if not os.path.exists(exe):
                return f"❌  No se encontró: {exe}"
            try:
                if args:
                    subprocess.Popen(f'"{exe}" {args}', shell=True)
                else:
                    subprocess.Popen(exe)
                return f"✅  {name} abierto"
            except Exception as e:
                return f"❌  Error al abrir {name}: {e}"
    return f"❌  {name} no está en la lista"


def close_game(name):
    games = _load()
    for g in games:
        if g["name"].lower() == name.lower():
            exe = os.path.basename(g["exe_path"])
            try:
                os.system(f"taskkill /f /im \"{exe}\" >nul 2>&1")
                return f"⏹  {name} cerrado"
            except Exception as e:
                return f"❌  Error al cerrar {name}: {e}"
    return f"❌  {name} no está en la lista"


def is_running(name):
    games = _load()
    for g in games:
        if g["name"].lower() == name.lower():
            exe = os.path.basename(g["exe_path"])
            for proc in psutil.process_iter(["name"]):
                try:
                    if proc.info["name"] and proc.info["name"].lower() == exe.lower():
                        return True
                except Exception:
                    pass
            return False
    return False


def scan_games():
    found = []
    scanned = set()

    def add_if_game(folder, exe_name):
        exe_path = os.path.join(folder, exe_name)
        if os.path.isfile(exe_path) and exe_path not in scanned:
            scanned.add(exe_path)
            name = os.path.splitext(exe_name)[0]
            found.append({"name": name, "exe_path": exe_path, "args": ""})

    def scan_folder(folder, depth=0):
        if depth > 2 or not os.path.isdir(folder):
            return
        try:
            for entry in os.listdir(folder):
                full = os.path.join(folder, entry)
                if os.path.isdir(full):
                    scan_folder(full, depth + 1)
                elif entry.lower().endswith(".exe") and entry not in (
                    "uninstall.exe", "setup.exe", "install.exe",
                    "dxsetup.exe", "vc_redist.exe", "dotnet*.exe",
                ):
                    # Skip common non-game executables
                    if any(kw in entry.lower() for kw in ("unins", "setup", "install", "redist", "dxsetup", "vc_redist")):
                        continue
                    name = os.path.splitext(entry)[0]
                    found.append({"name": name, "exe_path": full, "args": ""})
                    scanned.add(full)
        except PermissionError:
            pass
        except Exception:
            pass

    # 1) Steam
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            steam_path = winreg.QueryValueEx(key, "SteamPath")[0]
        games_dir = os.path.join(steam_path, "steamapps", "common")
        if os.path.isdir(games_dir):
            for gname in os.listdir(games_dir):
                gpath = os.path.join(games_dir, gname)
                if os.path.isdir(gpath):
                    # Find the main .exe
                    for f in os.listdir(gpath):
                        if f.lower().endswith(".exe") and f.lower() not in (
                            "uninstall.exe", "setup.exe",
                        ):
                            if any(kw in f.lower() for kw in ("unins", "setup", "install", "redist")):
                                continue
                            add_if_game(gpath, f)
                            break  # one exe per game folder
    except Exception:
        pass

    # 2) Common install dirs (top level only — fast)
    for root_dir in (
        os.environ.get("ProgramFiles", "C:\\Program Files"),
        os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
        os.environ.get("LocalAppData", ""),
        os.environ.get("AppData", ""),
    ):
        if root_dir and os.path.isdir(root_dir):
            try:
                for entry in os.listdir(root_dir):
                    full = os.path.join(root_dir, entry)
                    if os.path.isdir(full):
                        for f in os.listdir(full):
                            if f.lower().endswith(".exe") and f.lower() not in (
                                "uninstall.exe", "setup.exe",
                            ):
                                if any(kw in f.lower() for kw in ("unins", "setup", "install", "redist", "dxsetup")):
                                    continue
                                add_if_game(full, f)
                                break
            except PermissionError:
                pass

    return found


def list_games():
    games = _load()
    if not games:
        return "❌  No hay juegos configurados"
    lines = ["🎮  Juegos disponibles:"]
    for g in games:
        status = "🟢" if is_running(g["name"]) else "⚫"
        lines.append(f"  {status} {g['name']}")
    return "\n".join(lines)


def handle_command(text):
    text = text.strip().lower()
    m = re.match(r"^(abre|abrir|open|iniciar|cierra|cerrar|close|kill)\s+(.+)$", text)
    if not m:
        return None
    action, name = m.group(1), m.group(2).strip()
    games = _load()
    match = None
    for g in games:
        if g["name"].lower() == name or name in g["name"].lower():
            match = g["name"]
            break
    if not match:
        names = ", ".join(g["name"] for g in games)
        return f"❌  No encontré '{name}'. Juegos disponibles: {names}" if names else f"❌  No hay juegos configurados"
    if action in ("abre", "abrir", "open", "iniciar"):
        return open_game(match)
    else:
        return close_game(match)
