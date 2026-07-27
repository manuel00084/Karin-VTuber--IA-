from src.kste.translator.base_translator import ITranslator
from src.utils.log import warn


class ArgosTranslator(ITranslator):
    def __init__(self, api_key=""):
        self._pkg = None
        self._available = False
        self._init_argos()

    def _init_argos(self):
        try:
            import argostranslate.package
            import argostranslate.translate
            argostranslate.package.update_package_index()
            available = argostranslate.package.get_available_packages()
            self._available = True
            self._argo = argostranslate.translate
            self._pkg_mod = argostranslate.package
            self._available_pkgs = available
        except ImportError:
            warn("Argos Translate not installed. pip install argostranslate")
        except Exception as e:
            warn(f"Argos init error: {e}")

    @property
    def name(self):
        return "argos"

    @property
    def is_online(self):
        return False

    @property
    def requires_key(self):
        return False

    def translate(self, text, source="auto", target="es"):
        if not text or not text.strip():
            return ""
        if not self._available:
            raise RuntimeError("Argos Translate not available")
        try:
            installed = self._argo.get_installed_languages()
            src_lang = None
            tgt_lang = None
            for lang in installed:
                if lang.code == source:
                    src_lang = lang
                if lang.code == target:
                    tgt_lang = lang
            if not tgt_lang:
                raise ValueError(f"Target language '{target}' not installed in Argos")
            if not src_lang:
                src_lang = installed[0] if installed else None
            if not src_lang:
                raise ValueError("No source language available")
            return src_lang.get_translation(tgt_lang).translate(text)
        except Exception as e:
            warn(f"Argos translate error: {e}")
            return text

    def test(self):
        return self._available
