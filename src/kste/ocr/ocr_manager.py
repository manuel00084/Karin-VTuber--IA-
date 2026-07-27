from dataclasses import dataclass
from src.utils.log import warn


@dataclass
class OcrResult:
    texto: str
    bbox: tuple
    confianza: float


class OCRManager:
    def __init__(self, config):
        self.config = config
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            try:
                from src.utils.game_ocr_lite import get_game_ocr
                self._engine = get_game_ocr()
            except Exception as e:
                warn(f"KSTE OCR init error: {e}")
        return self._engine

    def read(self, image):
        if image is None:
            return []
        engine = self._get_engine()
        if engine is None:
            return []
        try:
            raw = engine.read_text(image)
            results = []
            for r in raw:
                if r.get("score", 0) >= self.config.ocr_confidence:
                    results.append(OcrResult(
                        texto=r["text"].strip(),
                        bbox=tuple(r["box"]),
                        confianza=r["score"]
                    ))
            return results
        except Exception as e:
            warn(f"KSTE OCR read error: {e}")
            return []

    def set_confidence(self, min_conf):
        self.config.ocr_confidence = min_conf
