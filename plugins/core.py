"""
plugins/core.py — Gestor de plugins con descubrimiento desde ZIP.

Cada plugin es un archivo .zip dentro de plugins/ con:
  manifest.json  — metadatos del plugin
  main.py        — código del plugin (entry point)
  ... otros archivos que necesite

Flujo:
  1. PluginManager.discover() escanea plugins/*.zip
  2. Extrae cada ZIP a plugins/_cache/<nombre>/
  3. Lee manifest.json y prepara PluginInfo
  4. PluginManager.load_all(api) carga cada plugin y llama on_load(api)
  5. En cada evento, el sistema llama a los hooks registrados
  6. Al cerrar, PluginManager.unload_all() llama on_unload()
"""

import os, json, importlib.util, sys, threading, traceback, zipfile, shutil
from collections import defaultdict
from packaging.version import Version

_PLUGINS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins")
_CACHE_DIR = os.path.join(_PLUGINS_DIR, "_cache")
_EXCLUDED = {"__pycache__", "__init__.py", "core.py", "api.py", "_cache"}
_APP_VERSION = "0.9.1"


class PluginInfo:
    """Metadatos de un plugin."""

    def __init__(self, manifest, directory, source_zip=""):
        self.name = manifest.get("name", "Desconocido")
        self.version = manifest.get("version", "0.0.0")
        self.api_version = manifest.get("api_version", "1")
        self.app_version_min = manifest.get("app_version_min", "0.0.0")
        self.author = manifest.get("author", "Anónimo")
        self.description = manifest.get("description", "")
        self.entry = manifest.get("entry", "main.py")
        self.dependencies = manifest.get("dependencies", {})
        self.hooks = manifest.get("hooks", [])
        self.gpu = manifest.get("gpu", False)
        self.ram_mb = manifest.get("resources_ram_mb", 0)
        self.directory = directory
        self.source_zip = source_zip
        self.enabled = True
        self.module = None
        self.instance = None


class PluginManager:
    """Singleton que gestiona todos los plugins cargados desde ZIP."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.plugins = []
        self._hooks = defaultdict(list)
        self._lock = threading.Lock()
        self._api = None

    # ── Descubrimiento ────────────────────────────────────────

    def discover(self):
        """Escanea plugins/*.zip, extrae a _cache/ y devuelve lista de PluginInfo."""
        self._limpiar_cache()
        os.makedirs(_CACHE_DIR, exist_ok=True)

        discovered = []
        if not os.path.isdir(_PLUGINS_DIR):
            return discovered

        for entry in os.listdir(_PLUGINS_DIR):
            if entry in _EXCLUDED or entry.startswith("_") or entry.startswith("."):
                continue

            zip_path = os.path.join(_PLUGINS_DIR, entry)
            if not zipfile.is_zipfile(zip_path):
                continue

            try:
                with zipfile.ZipFile(zip_path) as z:
                    names = z.namelist()
                    if "manifest.json" not in names:
                        print(f"[Plugins] {entry}: falta manifest.json, ignorado")
                        continue

                    nombre_base = entry.rsplit(".", 1)[0]
                    extract_dir = os.path.join(_CACHE_DIR, nombre_base)
                    if os.path.isdir(extract_dir):
                        shutil.rmtree(extract_dir)
                    z.extractall(extract_dir)

                    with open(os.path.join(extract_dir, "manifest.json"), "r", encoding="utf-8") as f:
                        manifest = json.load(f)

                info = PluginInfo(manifest, extract_dir, zip_path)
                discovered.append(info)
                print(f"[Plugins] Descubierto: {info.name} v{info.version} ({entry})")
            except Exception as e:
                print(f"[Plugins] Error procesando {entry}: {e}")

        self.plugins = discovered
        return discovered

    def _limpiar_cache(self):
        """Borra la caché de extracción de plugins."""
        if os.path.isdir(_CACHE_DIR):
            try:
                shutil.rmtree(_CACHE_DIR)
            except Exception as e:
                print(f"[Plugins] Error limpiando caché: {e}")

    # ── Carga ─────────────────────────────────────────────────

    def load_all(self, api):
        """Carga todos los plugins descubiertos."""
        self._api = api
        loaded = []
        for info in self.plugins:
            if not info.enabled:
                continue
            try:
                if info.app_version_min and info.app_version_min != "0.0.0":
                    if Version(_APP_VERSION) < Version(info.app_version_min):
                        raise RuntimeError(
                            f"Requiere app >= {info.app_version_min} (actual: {_APP_VERSION})"
                        )
                self._load_one(info)
                loaded.append(info.name)
                api.log(f"[Plugins] Cargado: {info.name} v{info.version}")
            except Exception as e:
                api.log(f"[Plugins] Error cargando {info.name}: {e}")
                traceback.print_exc()
        return loaded

    def _load_one(self, info):
        """Carga un plugin individual desde su directorio extraído."""
        entry_path = os.path.join(info.directory, info.entry)
        if not os.path.isfile(entry_path):
            raise FileNotFoundError(f"Entry no encontrado: {entry_path}")

        sys.path.insert(0, info.directory)

        spec = importlib.util.spec_from_file_location(
            f"plugin_{info.name}", entry_path
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"No se pudo crear spec para {entry_path}")

        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        info.module = mod

        if hasattr(mod, "on_load"):
            info.instance = mod.on_load(self._api) or mod
        else:
            info.instance = mod

        self._register_plugin_hooks(info)

        if info.directory in sys.path:
            sys.path.remove(info.directory)

    def _register_plugin_hooks(self, info):
        """Registra hooks del plugin."""
        mod = info.module
        if not mod:
            return
        for hook_name in info.hooks:
            func_name = f"on_{hook_name}"
            if hasattr(mod, func_name):
                self._hooks[hook_name].append((info, getattr(mod, func_name)))

    # ── Sistema de hooks ──────────────────────────────────────

    def hook(self, hook_name):
        """Decorador inline."""
        def decorator(func):
            self._hooks[hook_name].append((None, func))
            return func
        return decorator

    def register_hook(self, hook_name, callback):
        self._hooks[hook_name].append((None, callback))

    def emit(self, hook_name, *args, **kwargs):
        """Ejecuta todos los callbacks registrados para un hook."""
        results = []
        for plugin, callback in self._hooks.get(hook_name, []):
            if plugin is not None and not plugin.enabled:
                continue
            try:
                result = callback(*args, **kwargs)
                if result is not None:
                    results.append(result)
            except Exception as e:
                if self._api:
                    self._api.log(
                        f"[Plugins] Error en hook '{hook_name}' de "
                        f"{plugin.name if plugin else 'desconocido'}: {e}"
                    )
                traceback.print_exc()
        return results

    def emit_first(self, hook_name, *args, **kwargs):
        """Short-circuit: ejecuta hooks hasta que uno devuelva algo."""
        for plugin, callback in self._hooks.get(hook_name, []):
            if plugin is not None and not plugin.enabled:
                continue
            try:
                result = callback(*args, **kwargs)
                if result is not None:
                    return result
            except Exception as e:
                if self._api:
                    self._api.log(f"[Plugins] Error en hook '{hook_name}': {e}")
        return None

    # ── Ciclo de vida ─────────────────────────────────────────

    def unload_all(self):
        """Descarga todos los plugins y limpia caché."""
        for info in self.plugins:
            if info.module and hasattr(info.module, "on_unload"):
                try:
                    info.module.on_unload()
                except Exception as e:
                    print(f"[Plugins] Error en on_unload de {info.name}: {e}")
        self._hooks.clear()
        self.plugins.clear()
        self._limpiar_cache()
        print("[Plugins] Todos los plugins descargados.")

    def reload_all(self):
        """Recarga todos los plugins."""
        self.unload_all()
        self.discover()
        if self._api:
            self.load_all(self._api)

    # ── Estado ────────────────────────────────────────────────

    def get_plugins_info(self):
        return [
            {
                "name": p.name,
                "version": p.version,
                "author": p.author,
                "description": p.description,
                "hooks": p.hooks,
                "gpu": p.gpu,
                "ram_mb": p.ram_mb,
                "enabled": p.enabled,
                "loaded": p.module is not None,
            }
            for p in self.plugins
        ]
