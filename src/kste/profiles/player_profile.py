import json, os, time
from dataclasses import dataclass, field, asdict
from src import PROJECT_ROOT
from src.utils.log import info, error

_DATA_DIR = os.path.join(PROJECT_ROOT, "data")
_PROFILES_PATH = os.path.join(_DATA_DIR, "kste_profiles.json")


@dataclass
class PlayerProfile:
    nombre: str
    idioma_detectado: str = "unknown"
    ultimo_idioma: str = "unknown"
    ultimo_visto: float = 0.0
    mensajes_totales: int = 0
    canal_favorito: str = "general"
    idioma_confianza: float = 0.0


class PlayerProfileManager:
    def __init__(self):
        self._profiles = {}
        self.load()

    def get(self, player_name):
        return self._profiles.get(player_name)

    def get_or_create(self, player_name):
        if player_name not in self._profiles:
            self._profiles[player_name] = PlayerProfile(
                nombre=player_name,
                ultimo_visto=time.time()
            )
        return self._profiles[player_name]

    def update(self, player_name, **kwargs):
        profile = self.get_or_create(player_name)
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        profile.ultimo_visto = time.time()

    def set_language(self, player_name, lang, confidence=0.0):
        profile = self.get_or_create(player_name)
        profile.ultimo_idioma = profile.idioma_detectado
        profile.idioma_detectado = lang
        profile.idioma_confianza = confidence

    def search(self, query):
        query_lower = query.lower()
        return [p for p in self._profiles.values()
                if query_lower in p.nombre.lower()]

    def all_profiles(self):
        return list(self._profiles.values())

    def save(self):
        try:
            os.makedirs(_DATA_DIR, exist_ok=True)
            data = {}
            for name, p in self._profiles.items():
                data[name] = asdict(p)
            with open(_PROFILES_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            info(f"KSTE profiles saved: {len(data)}")
        except Exception as e:
            error(f"KSTE profiles save: {e}")

    def load(self):
        try:
            if os.path.exists(_PROFILES_PATH):
                with open(_PROFILES_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for name, d in data.items():
                    self._profiles[name] = PlayerProfile(**{
                        k: v for k, v in d.items()
                        if k in PlayerProfile.__dataclass_fields__
                    })
                info(f"KSTE profiles loaded: {len(self._profiles)}")
        except Exception as e:
            error(f"KSTE profiles load: {e}")
            self._profiles = {}
