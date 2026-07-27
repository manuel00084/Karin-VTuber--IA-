import os
import base64
import hashlib
import shutil
import json
import threading
import time
from src.utils.log import error, info, warn
from src import PROJECT_ROOT

CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "config.txt")
SECRETS_PATH = os.path.join(PROJECT_ROOT, "config", "secrets.enc")

_DEFAULT_ENCRYPTION_KEY = "KarinVTuber2024SecretKey!"
ENCRYPTION_PASSWORD = os.environ.get("KARIN_ENCRYPTION_KEY", _DEFAULT_ENCRYPTION_KEY)
if ENCRYPTION_PASSWORD == _DEFAULT_ENCRYPTION_KEY:
    warn("[ENCRYPTION] Usando clave por defecto. Define KARIN_ENCRYPTION_KEY en variable de entorno.")

SENSITIVE_KEYS = {
    "TWITCH_CLIENT_ID", "TWITCH_CLIENT_SECRET", "TWITCH_TOKEN",
    "GROQ_API_KEY", "CEREBRAS_API_KEY", "GOOGLE_STUDIO_API_KEY",
    "FISH_API_KEY", "LOCAL_AI_API_KEY",
    "OBS_PASSWORD",
    "DISCORD_BOT_TOKEN",
}


def _get_key():
    key = hashlib.sha256(ENCRYPTION_PASSWORD.encode()).digest()
    return base64.urlsafe_b64encode(key)

def _load_secrets():
    if not os.path.exists(SECRETS_PATH):
        return {}
    try:
        with open(SECRETS_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            from cryptography.fernet import Fernet
            fernet = Fernet(_get_key())
            data = base64.b64decode(content)
            decrypted = fernet.decrypt(data).decode()
            secrets = {}
            for line in decrypted.split("\n"):
                if "=" in line:
                    k, v = line.split("=", 1)
                    secrets[k.strip()] = v.strip()
            return secrets
    except Exception:
        return {}

def _save_secrets(secrets):
    from cryptography.fernet import Fernet
    fernet = Fernet(_get_key())
    raw = "\n".join(f"{k}={v}" for k, v in secrets.items())
    encrypted = fernet.encrypt(raw.encode())
    encoded = base64.b64encode(encrypted).decode()
    with open(SECRETS_PATH, "w", encoding="utf-8") as f:
        f.write(encoded)

def get_secret(key_name):
    secrets = _load_secrets()
    return secrets.get(key_name)

def set_secret(key_name, value):
    secrets = _load_secrets()
    secrets[key_name] = value
    _save_secrets(secrets)

def clear_secret(key_name):
    secrets = _load_secrets()
    if key_name in secrets:
        del secrets[key_name]
        _save_secrets(secrets)

def _load_config():
    cfg = {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    cfg[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return cfg

def _normalizar_voz(voz):
    """Convierte es_MX-Name → es-MX-Name (guión bajo a guión)"""
    if isinstance(voz, str) and "_" in voz:
        partes = voz.split("-", 1)
        if len(partes) == 2 and "_" in partes[0]:
            partes[0] = partes[0].replace("_", "-")
            return "-".join(partes)
    return voz

def load_config():
    cfg = _load_config()
    secrets = _load_secrets()
    cfg.update(secrets)
    for k in list(cfg.keys()):
        if "VOICE" in k.upper() or k in ("COMENTARISTA_VOICE", "SUBTITULOS_VOICE",
                                          "BOT_IA_VOICE", "BOT_VOICE_MALE", "BOT_VOICE_FEMALE"):
            cfg[k] = _normalizar_voz(cfg.get(k, ""))
    return cfg

def save_config(config):
    _ensure_backup_thread()
    non_sensitive = {}
    sensitive_updates = {}
    for k, v in config.items():
        val = _normalizar_voz(str(v).strip()) if "VOICE" in k.upper() else str(v).strip()
        if not val:
            continue
        if k in SENSITIVE_KEYS:
            sensitive_updates[k] = val
        else:
            non_sensitive[k] = val
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            for k, v in non_sensitive.items():
                f.write(f"{k}={v}\n")
    except Exception as e:
        error(f"Error guardando config: {e}")
    secrets = _load_secrets()
    changed = False
    for k, v in sensitive_updates.items():
        if secrets.get(k) != v:
            secrets[k] = v
            changed = True
    if changed:
        _save_secrets(secrets)


def _migrate_plaintext_secrets():
    """Move API keys from config.txt to secrets.enc and remove from config.txt"""
    if not os.path.exists(CONFIG_PATH):
        return
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        secrets = _load_secrets()
        changed_secrets = False
        new_lines = []
        migrated = False
        for line in lines:
            stripped = line.strip()
            if "=" in stripped:
                k, v = stripped.split("=", 1)
                k = k.strip()
                v = v.strip()
                if k in SENSITIVE_KEYS and v:
                    if secrets.get(k) != v:
                        secrets[k] = v
                        changed_secrets = True
                    migrated = True
                    continue
            new_lines.append(line)
        if migrated:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            info(f"Migradas {sum(1 for l in lines if '=' in l and l.split('=',1)[0].strip() in SENSITIVE_KEYS)} claves de config.txt a secrets.enc")
        if changed_secrets:
            _save_secrets(secrets)
    except Exception as e:
        error(f"Error migrando secretos: {e}")

_migrate_plaintext_secrets()

# ── Auto-backup ──────────────────────────────────────────

BACKUP_DIR = os.path.join(PROJECT_ROOT, "backups")
_CONFIG_BACKUP_INTERVAL = 1800  # 30 min


def _backup_file(src, dest_name):
    if not os.path.exists(src):
        return
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        dest = os.path.join(BACKUP_DIR, f"{dest_name}.{ts}.bak")
        shutil.copy2(src, dest)
        # Keep only last 10 backups per file
        prefix = f"{dest_name}."
        backups = sorted(
            [f for f in os.listdir(BACKUP_DIR) if f.startswith(prefix)],
            reverse=True,
        )
        for old in backups[10:]:
            try:
                os.remove(os.path.join(BACKUP_DIR, old))
            except Exception:
                pass
    except Exception as e:
        error(f"Backup failed for {dest_name}: {e}")


def do_backup():
    _backup_file(CONFIG_PATH, "config")
    _backup_file(SECRETS_PATH, "secrets")
    mem_file = os.path.join(PROJECT_ROOT, "data", "memory.json")
    _backup_file(mem_file, "memory")
    vec_file = os.path.join(PROJECT_ROOT, "data", "vector_memory_fallback.json")
    _backup_file(vec_file, "vector_memory")
    info("✅ Backup automático completado")


def _backup_loop():
    while True:
        time.sleep(_CONFIG_BACKUP_INTERVAL)
        do_backup()


_backup_started = False

def _ensure_backup_thread():
    global _backup_started
    if not _backup_started:
        _backup_started = True
        t = threading.Thread(target=_backup_loop, daemon=True)
        t.start()

# ── Profiles ──────────────────────────────────────────

PROFILES_DIR = os.path.join(PROJECT_ROOT, "config", "profiles")


def _ensure_profiles_dir():
    os.makedirs(PROFILES_DIR, exist_ok=True)


def list_profiles():
    _ensure_profiles_dir()
    profiles = []
    for f in os.listdir(PROFILES_DIR):
        if f.endswith(".json"):
            profiles.append(f[:-5])
    return sorted(profiles)


def save_profile(name):
    _ensure_profiles_dir()
    cfg = _load_config()
    secrets = _load_secrets()
    profile = {"config": cfg, "secrets": _encrypt_secrets_for_export(secrets)}
    path = os.path.join(PROFILES_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    info(f"✅ Perfil '{name}' guardado")


def load_profile(name):
    path = os.path.join(PROFILES_DIR, f"{name}.json")
    if not os.path.exists(path):
        return False
    with open(path, "r", encoding="utf-8") as f:
        profile = json.load(f)
    cfg = profile.get("config", {})
    secrets = profile.get("secrets", {})
    # Handle both encrypted and legacy plain-text profiles
    if isinstance(secrets, dict) and secrets.get("_encrypted"):
        secrets = _decrypt_secrets_from_export(secrets)
    # Write config
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        for k, v in cfg.items():
            f.write(f"{k}={v}\n")
    # Write secrets
    _save_secrets(secrets)
    info(f"✅ Perfil '{name}' cargado")
    return True


def _encrypt_secrets_for_export(secrets):
    """Encrypt secrets dict for profile export using Fernet."""
    if not secrets:
        return {}
    try:
        from cryptography.fernet import Fernet
        fernet = Fernet(_get_key())
        raw = json.dumps(secrets, ensure_ascii=False)
        encrypted = fernet.encrypt(raw.encode())
        return {"_encrypted": True, "data": base64.b64encode(encrypted).decode()}
    except Exception:
        # Fallback: store as plain (legacy compatibility)
        return secrets


def _decrypt_secrets_from_export(encrypted_obj):
    """Decrypt secrets dict from profile export."""
    data_b64 = encrypted_obj.get("data", "")
    if not data_b64:
        return {}
    try:
        from cryptography.fernet import Fernet
        fernet = Fernet(_get_key())
        decrypted = fernet.decrypt(base64.b64decode(data_b64)).decode()
        return json.loads(decrypted)
    except Exception:
        return {}


def delete_profile(name):
    path = os.path.join(PROFILES_DIR, f"{name}.json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def export_profile(name, export_path):
    _ensure_profiles_dir()
    src = os.path.join(PROFILES_DIR, f"{name}.json")
    if os.path.exists(src):
        shutil.copy2(src, export_path)
        return True
    return False


def import_profile(import_path):
    _ensure_profiles_dir()
    if not os.path.exists(import_path):
        return None
    base = os.path.splitext(os.path.basename(import_path))[0]
    dest = os.path.join(PROFILES_DIR, f"{base}.json")
    shutil.copy2(import_path, dest)
    return base