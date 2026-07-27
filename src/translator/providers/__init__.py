from .gemini import GeminiProvider
from .deepl import DeepLProvider
from .google_web import GoogleWebProvider
from .dummy import DummyProvider

PROVIDERS = {
    "google_gemini": GeminiProvider,
    "deepl": DeepLProvider,
    "google_web": GoogleWebProvider,
    "dummy": DummyProvider,
}

def get_provider(name, api_key=None):
    cls = PROVIDERS.get(name)
    if not cls:
        cls = DummyProvider
    return cls(api_key)
