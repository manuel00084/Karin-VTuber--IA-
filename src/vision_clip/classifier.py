import os
import numpy as np
from PIL import Image
import cv2

from .prompts import SCENE_PROMPTS

MOBILECLIP_OK = False
try:
    import mobileclip
    import torch
    MOBILECLIP_OK = True
except ImportError:
    pass

MODEL_URLS = {
    "mobileclip_s0": "https://huggingface.co/apple/MobileCLIP-S0/resolve/main/mobileclip_s0.pt",
    "mobileclip_s1": "https://huggingface.co/apple/MobileCLIP-S1/resolve/main/mobileclip_s1.pt",
    "mobileclip_s2": "https://huggingface.co/apple/MobileCLIP-S2/resolve/main/mobileclip_s2.pt",
}

_MODEL_DIR = None


def _get_model_dir():
    global _MODEL_DIR
    if _MODEL_DIR is None:
        _MODEL_DIR = os.path.join(os.path.dirname(__file__), "_weights")
        os.makedirs(_MODEL_DIR, exist_ok=True)
    return _MODEL_DIR


def _download_progress(url, dest):
    import requests
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    downloaded = 0
    chunk_size = 8192
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total and total > 0:
                    pct = int(100 * downloaded / total)
                    print(f"\r Descargando... {pct}% ({downloaded//1024**2}MB/{total//1024**2}MB)", end="")
    print()


def descargar_modelo(model_name="mobileclip_s2"):
    url = MODEL_URLS.get(model_name)
    if not url:
        raise ValueError(f"Modelo desconocido: {model_name}. Opciones: {list(MODEL_URLS.keys())}")
    dest = os.path.join(_get_model_dir(), f"{model_name}.pt")
    if os.path.exists(dest):
        return dest
    print(f" Descargando {model_name} desde HuggingFace...")
    _download_progress(url, dest)
    print(f" Modelo guardado en: {dest}")
    return dest


class CLIPSceneAnalyzer:
    def __init__(self, model_name="mobileclip_s2", prompts=None, confianza_min=0.15):
        self.confianza_min = confianza_min
        self.prompts = prompts or SCENE_PROMPTS
        self._prompt_cache = {}

        if not MOBILECLIP_OK:
            raise ImportError(
                "mobileclip no instalado. Ejecuta:\n"
                "  pip install git+https://github.com/apple/ml-mobileclip.git\n"
                "  pip install torch --index-url https://download.pytorch.org/whl/cpu"
            )

        model_path = os.path.join(_get_model_dir(), f"{model_name}.pt")
        if not os.path.exists(model_path):
            model_path = descargar_modelo(model_name)

        self.model, _, self.preprocess = mobileclip.create_model_and_transforms(
            model_name, pretrained=model_path
        )
        self.model.eval()
        self.tokenizer = mobileclip.get_tokenizer(model_name)
        self.model_name = model_name

    def _encode_texts(self, texts):
        tokens = self.tokenizer(texts)
        with torch.no_grad():
            feats = self.model.encode_text(tokens)
            feats = feats / feats.norm(dim=-1, keepdim=True)
        return feats

    def _cached_prompts(self, category):
        if category not in self._prompt_cache:
            prompts = self.prompts.get(category, [])
            if prompts:
                self._prompt_cache[category] = self._encode_texts(prompts)
        return self._prompt_cache.get(category)

    def analizar(self, image):
        if isinstance(image, np.ndarray):
            image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        img_tensor = self.preprocess(image).unsqueeze(0)
        with torch.no_grad():
            img_feats = self.model.encode_image(img_tensor)
            img_feats = img_feats / img_feats.norm(dim=-1, keepdim=True)

        resultados = {}
        for category in self.prompts:
            text_feats = self._cached_prompts(category)
            if text_feats is None:
                continue
            sim = (img_feats @ text_feats.T).squeeze(0)
            probs = sim.softmax(dim=-1)
            scores = {self.prompts[category][i]: float(probs[i]) for i in range(len(self.prompts[category]))}
            resultados[category] = scores

        return resultados

    def escena_detectada(self, image):
        res = self.analizar(image)
        info = {}

        if "estados" in res:
            top_estado = max(res["estados"], key=lambda k: res["estados"][k])
            conf = res["estados"][top_estado]
            if conf > self.confianza_min:
                info["estado"] = top_estado
                info["estado_conf"] = conf

        if "escenarios" in res:
            top_escena = max(res["escenarios"], key=lambda k: res["escenarios"][k])
            conf = res["escenarios"][top_escena]
            if conf > self.confianza_min:
                info["escenario"] = top_escena
                info["escenario_conf"] = conf

        if "personajes" in res:
            info["entidades"] = res["personajes"]

        if "efectos" in res:
            top_efecto = max(res["efectos"], key=lambda k: res["efectos"][k])
            conf = res["efectos"][top_efecto]
            if conf > self.confianza_min:
                info["efecto"] = top_efecto
                info["efecto_conf"] = conf

        if "ui" in res:
            info["ui"] = res["ui"]

        return info

    def generar_resumen(self, image):
        info = self.escena_detectada(image)
        partes = []

        estado = info.get("estado", "")
        escenario = info.get("escenario", "")
        efecto = info.get("efecto", "")

        if escenario:
            partes.append(f"Escenario: {escenario}")
        if estado:
            partes.append(f"Estado: {estado}")
        if efecto:
            partes.append(f"Efecto: {efecto}")

        entidades = info.get("entidades", {})
        if entidades:
            top = max(entidades, key=entidades.get)
            if entidades[top] > 0.2:
                partes.append(f"Personaje: {top}")

        ui = info.get("ui", {})
        uis_presentes = [k for k, v in ui.items() if v > 0.15]
        if uis_presentes:
            partes.append(f"UI: {', '.join(uis_presentes[:3])}")

        return ". ".join(partes) if partes else ""

    def resumen_para_ia(self, image):
        info = self.escena_detectada(image)
        ctx = ""

        estado = info.get("estado", "")
        escenario = info.get("escenario", "")
        efecto = info.get("efecto", "")

        if escenario:
            ctx += f"Estamos en {escenario}. "
        if estado:
            ctx += f"Estado: {estado}. "
        if efecto:
            ctx += f"Efecto visual: {efecto}. "

        entidades = info.get("entidades", {})
        top_ent = max(entidades, key=entidades.get) if entidades else ""
        if top_ent and entidades[top_ent] > 0.2:
            ctx += f"Veo {top_ent}. "

        ui = info.get("ui", {})
        uis_presentes = [k for k, v in ui.items() if v > 0.15]
        if uis_presentes:
            ctx += f"En pantalla: {', '.join(uis_presentes[:3])}. "

        return ctx
