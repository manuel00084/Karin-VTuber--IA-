from src.kste.translator.base_translator import ITranslator
from src.utils.log import warn


class NLLBTranslator(ITranslator):
    def __init__(self, api_key=""):
        self._model = None
        self._processor = None
        self._available = False
        self._init_nllb()

    def _init_nllb(self):
        try:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            model_name = "facebook/nllb-200-distilled-600M"
            self._processor = AutoTokenizer.from_pretrained(model_name)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            self._available = True
        except ImportError:
            warn("NLLB requires transformers. pip install transformers torch")
        except Exception as e:
            warn(f"NLLB init error: {e}")

    @property
    def name(self):
        return "nllb"

    @property
    def is_online(self):
        return False

    @property
    def requires_key(self):
        return False

    _LANG_MAP = {
        "es": "spa_Latn", "en": "eng_Latn", "ja": "jpn_Jpan",
        "ko": "kor_Hang", "zh": "zho_Hans", "pt": "por_Latn",
        "fr": "fra_Latn", "de": "deu_Latn", "it": "ita_Latn",
        "ru": "rus_Cyrl", "ar": "arb_Arab", "hi": "hin_Deva",
    }

    def translate(self, text, source="auto", target="es"):
        if not text or not text.strip():
            return ""
        if not self._available:
            raise RuntimeError("NLLB model not loaded")
        try:
            src_code = self._LANG_MAP.get(source, "eng_Latn")
            tgt_code = self._LANG_MAP.get(target, "spa_Latn")
            self._processor.src_lang = src_code
            inputs = self._processor(text, return_tensors="pt")
            translated_tokens = self._model.generate(
                **inputs,
                forced_bos_token_id=self._processor.lang_code_to_id[tgt_code],
                max_length=512,
            )
            result = self._processor.batch_decode(
                translated_tokens, skip_special_tokens=True
            )[0]
            return result
        except Exception as e:
            warn(f"NLLB translate error: {e}")
            return text

    def test(self):
        return self._available
