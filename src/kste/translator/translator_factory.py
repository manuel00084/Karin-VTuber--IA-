from src.utils.log import info, warn
from src.kste.translator.base_translator import ITranslator

_REGISTRY = {}


def register(name, cls):
    _REGISTRY[name] = cls


def create(name, api_key=""):
    if name not in _REGISTRY:
        available = list(_REGISTRY.keys())
        warn(f"Unknown translator: {name}. Available: {available}")
        if available:
            name = available[0]
            info(f"Falling back to: {name}")
        else:
            raise ValueError("No translators registered")
    cls = _REGISTRY[name]
    try:
        return cls(api_key=api_key)
    except TypeError:
        return cls()


def available():
    return list(_REGISTRY.keys())


def _register_defaults():
    from src.kste.translator.google_translator import GoogleTranslator
    from src.kste.translator.deepl_translator import DeepLTranslator
    from src.kste.translator.argos_translator import ArgosTranslator
    from src.kste.translator.libre_translator import LibreTranslator
    from src.kste.translator.nllb_translator import NLLBTranslator
    register("google", GoogleTranslator)
    register("deepl", DeepLTranslator)
    register("argos", ArgosTranslator)
    register("libre", LibreTranslator)
    register("nllb", NLLBTranslator)


_register_defaults()
