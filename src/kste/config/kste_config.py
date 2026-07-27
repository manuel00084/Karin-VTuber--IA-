import json, os
from dataclasses import dataclass, field, asdict
from src import PROJECT_ROOT
from src.utils.log import info, error

_CONFIG_DIR = os.path.join(PROJECT_ROOT, "data")
_CONFIG_PATH = os.path.join(_CONFIG_DIR, "kste_config.json")


@dataclass
class KSTEConfig:
    capture_region: tuple = None
    capture_interval: float = 2.0
    ocr_confidence: float = 0.3
    translator_name: str = "google"
    translator_api_key: str = ""
    source_lang: str = "auto"
    target_lang: str = "es"
    cache_ttl_days: int = 30
    cache_max_entries: int = 10000
    overlay_opacity: float = 0.85
    overlay_font_size: int = 14
    overlay_position: tuple = (100, 100)
    overlay_text_color: str = "#00ff00"
    overlay_bg_color: str = "#1a1a2e"
    overlay_border_color: str = "#a855f7"
    spam_filter_enabled: bool = True
    min_message_length: int = 2
    auto_paste: bool = True
    auto_send_enter: bool = False
    history_max_days: int = 30

    def to_dict(self):
        d = asdict(self)
        for k, v in d.items():
            if isinstance(v, tuple):
                d[k] = list(v)
        return d

    @classmethod
    def from_dict(cls, d):
        if not d:
            return cls()
        for k in ("capture_region", "overlay_position"):
            if k in d and isinstance(d[k], list):
                d[k] = tuple(d[k])
        valid = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in valid}
        return cls(**filtered)


def load_kste_config():
    try:
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                return KSTEConfig.from_dict(json.load(f))
    except Exception as e:
        error(f"KSTE load_kste_config: {e}")
    return KSTEConfig()


def save_kste_config(config):
    try:
        os.makedirs(_CONFIG_DIR, exist_ok=True)
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
        info("KSTE config saved")
    except Exception as e:
        error(f"KSTE save_kste_config: {e}")
