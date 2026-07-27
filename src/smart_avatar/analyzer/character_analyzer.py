"""CharacterAnalyzer – analiza imagen de avatar con MediaPipe Face Mesh y heurísticas."""

from __future__ import annotations

import enum
import logging
from pathlib import Path
from typing import Sequence

import cv2
import numpy as np

from src.smart_avatar.core.interfaces import IAnalyzer
from src.smart_avatar.core.types import (
    AnalysisResult,
    BodyPartType,
    BodyRegion,
    Vec2,
)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Heurísticas de proporción corporativa (fracciones de la altura de la imagen)
# ---------------------------------------------------------------------------

class _BodyProportions(enum.Enum):
    """Referencia vertical relativa para ubicar regiones del cuerpo."""
    HAIR_TOP = 0.0
    HEAD_TOP = 0.05
    CHIN = 0.25
    SHOULDERS = 0.30
    CHEST = 0.35
    WAIST = 0.50
    HIPS = 0.55
    KNEES = 0.75
    FEET = 1.0


# ---------------------------------------------------------------------------
# MediaPipe Face Mesh landmark index ranges (468 landmarks)
# ---------------------------------------------------------------------------

class _FMeshIdx:
    """Índices de landmarks de MediaPipe Face Mesh agrupados por zona facial."""
    LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
    RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
    LEFT_EYEBROW = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
    RIGHT_EYEBROW = [300, 293, 334, 296, 336, 285, 295, 282, 283, 276]
    NOSE = [1, 2, 98, 327, 168, 6, 197, 195, 5, 4, 19, 94, 2]
    MOUTH = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 270, 269, 267, 0, 37, 39, 40, 185]
    JAW = [
        172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365,
        397, 288, 361, 323, 454, 356, 389, 251, 284, 332, 297, 338,
        234, 127, 162, 21, 54, 103, 67, 109, 10,
    ]
    FACE_OVAL = [
        10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
        397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
        172, 138, 213, 192, 134, 51, 5, 4, 19, 94, 2, 327, 298,
    ]

    @classmethod
    def _landmarks_for(cls, indices: Sequence[int],
                        landmarks: Sequence) -> list[Vec2]:
        return [
            Vec2(landmarks[i].x, landmarks[i].y) for i in indices if i < len(landmarks)
        ]

    @classmethod
    def bbox_for(cls, indices: Sequence[int],
                 landmarks: Sequence,
                 img_w: int, img_h: int) -> tuple[int, int, int, int]:
        xs, ys = [], []
        for i in indices:
            if i < len(landmarks):
                xs.append(int(landmarks[i].x * img_w))
                ys.append(int(landmarks[i].y * img_h))
        if not xs:
            return (0, 0, 0, 0)
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        return (x0, y0, x1 - x0, y1 - y0)


# ---------------------------------------------------------------------------
# Color clustering simple (K-means via OpenCV)
# ---------------------------------------------------------------------------

def _dominant_color(region_img: np.ndarray, k: int = 3) -> tuple[int, int, int]:
    """Devuelve el color dominante de *region_img* (BGR) como tupla (B, G, R)."""
    if region_img.size == 0:
        return (0, 0, 0)
    small = cv2.resize(region_img, (64, 64)) if region_img.shape[0] > 64 else region_img
    flat = small.reshape(-1, 3).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    try:
        _, labels, centers = cv2.kmeans(
            flat, k, None, criteria, 5, cv2.KMEANS_PP_CENTERS,
        )
        counts = np.bincount(labels.ravel())
        dominant = centers[counts.argmax()].astype(int)
        return (int(dominant[0]), int(dominant[1]), int(dominant[2]))
    except cv2.error:
        avg = flat.mean(axis=0).astype(int)
        return (int(avg[0]), int(avg[1]), int(avg[2]))


def _color_distance(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
    return float(np.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2))))


# ---------------------------------------------------------------------------
# CharacterAnalyzer
# ---------------------------------------------------------------------------

class CharacterAnalyzer(IAnalyzer):
    """Analiza una imagen de referencia y devuelve regiones corporales.

    Estrategia:
    1. Intentar MediaPipe Face Mesh para detección facial precisa.
    2. Derivar regiones del cuerpo mediante heurísticas de proporción.
    3. Fallback: si MediaPipe falla, usar bordes y segmentación por color.
    """

    def __init__(self, min_detection_confidence: float = 0.5) -> None:
        self._min_confidence = min_detection_confidence
        self._face_mesh = None
        self._mediapipe_ok = self._init_mediapipe()

    # ------------------------------------------------------------------
    # Inicialización de MediaPipe (lazy, tolerante a errores)
    # ------------------------------------------------------------------

    def _init_mediapipe(self) -> bool:
        try:
            import mediapipe as mp  # noqa: F811
            self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=self._min_confidence,
            )
            return True
        except Exception:
            log.warning("MediaPipe Face Mesh no disponible – usando heurísticas de fallback")
            return False

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def analyze(self, image_path: str) -> AnalysisResult:
        """Analiza *image_path* y devuelve las regiones detectadas."""
        path = Path(image_path)
        if not path.exists():
            log.error("Imagen no encontrada: %s", image_path)
            return AnalysisResult()

        img_bgr = cv2.imread(str(path))
        if img_bgr is None:
            log.error("No se pudo leer la imagen: %s", image_path)
            return AnalysisResult()

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        h, w = img_rgb.shape[:2]
        img_size = (w, h)

        regions: list[BodyRegion] = []

        # --- 1. Face landmarks ---
        face_landmarks: list[Vec2] = []
        face_bbox = (0, 0, 0, 0)
        if self._mediapipe_ok and self._face_mesh is not None:
            face_landmarks, face_bbox = self._detect_face_mediapipe(img_rgb, w, h)

        if face_landmarks:
            regions.extend(self._build_face_subregions(face_landmarks, face_bbox, w, h))
            regions.append(BodyRegion(
                type=BodyPartType.HEAD,
                bbox=face_bbox,
                confidence=0.95,
                landmarks=face_landmarks,
            ))
        else:
            face_bbox = self._detect_face_fallback(img_bgr)
            if face_bbox[2] > 0:
                regions.append(BodyRegion(
                    type=BodyPartType.HEAD,
                    bbox=face_bbox,
                    confidence=0.45,
                ))

        # --- 2. Hair ---
        hair_region = self._detect_hair(img_bgr, img_rgb, face_bbox, w, h)
        if hair_region:
            regions.append(hair_region)

        # --- 3. Cuerpo (heurísticas proporcionales) ---
        body_regions = self._estimate_body_regions(face_bbox, w, h)
        regions.extend(body_regions)

        # --- 4. Background ---
        bg_bbox = (0, 0, w, h)
        regions.append(BodyRegion(
            type=BodyPartType.ACCESSORY,
            bbox=bg_bbox,
            confidence=0.3,
        ))

        return AnalysisResult(
            regions=regions,
            image_size=img_size,
            character_type=self._guess_character_type(img_bgr),
        )

    # ------------------------------------------------------------------
    # MediaPipe face detection
    # ------------------------------------------------------------------

    def _detect_face_mediapipe(
        self, img_rgb: np.ndarray, w: int, h: int,
    ) -> tuple[list[Vec2], tuple[int, int, int, int]]:
        try:
            results = self._face_mesh.process(img_rgb)  # type: ignore[union-attr]
        except Exception as exc:
            log.warning("MediaPipe procesamiento falló: %s", exc)
            return [], (0, 0, 0, 0)

        if not results or not results.multi_face_landmarks:
            return [], (0, 0, 0, 0)

        lm = results.multi_face_landmarks[0].landmark
        all_lmarks = [
            Vec2(l.x, l.y) for l in lm
        ]
        face_bbox = _FMeshIdx.bbox_for(
            _FMeshIdx.FACE_OVAL, lm, w, h,
        )
        return all_lmarks, face_bbox

    def _build_face_subregions(
        self,
        landmarks: list[Vec2],
        face_bbox: tuple[int, int, int, int],
        w: int,
        h: int,
    ) -> list[BodyRegion]:
        """Construye sub-regiones faciales a partir de los landmarks."""
        fb_x, fb_y, fb_w, fb_h = face_bbox
        regions: list[BodyRegion] = []
        if fb_w == 0 or fb_h == 0:
            return regions

        # Para landmarks de MediaPipe, reconstruimos las coordenadas en píxeles
        # a partir de Vec2 normalizado
        def _lm_bbox(indices: Sequence[int]) -> tuple[int, int, int, int]:
            xs = [int(landmarks[i].x * w) for i in indices if i < len(landmarks)]
            ys = [int(landmarks[i].y * h) for i in indices if i < len(landmarks)]
            if not xs:
                return (0, 0, 0, 0)
            x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
            return (x0, y0, x1 - x0, y1 - y0)

        def _lm_pts(indices: Sequence[int]) -> list[Vec2]:
            return [landmarks[i] for i in indices if i < len(landmarks)]

        sub = [
            (BodyPartType.LEFT_EYE, _FMeshIdx.LEFT_EYE),
            (BodyPartType.RIGHT_EYE, _FMeshIdx.RIGHT_EYE),
            (BodyPartType.LEFT_EYEBROW, _FMeshIdx.LEFT_EYEBROW),
            (BodyPartType.RIGHT_EYEBROW, _FMeshIdx.RIGHT_EYEBROW),
            (BodyPartType.NOSE, _FMeshIdx.NOSE),
            (BodyPartType.MOUTH, _FMeshIdx.MOUTH),
        ]
        for part_type, idxs in sub:
            bbox = _lm_bbox(idxs)
            if bbox[2] > 0:
                regions.append(BodyRegion(
                    type=part_type,
                    bbox=bbox,
                    confidence=0.90,
                    landmarks=_lm_pts(idxs),
                ))
        return regions

    # ------------------------------------------------------------------
    # Fallback face detection (Haar cascade)
    # ------------------------------------------------------------------

    def _detect_face_fallback(self, img_bgr: np.ndarray) -> tuple[int, int, int, int]:
        try:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"  # type: ignore[attr-defined]
            face_cascade = cv2.CascadeClassifier(cascade_path)
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
            if len(faces) > 0:
                x, y, fw, fh = faces[0]
                return (int(x), int(y), int(fw), int(fh))
        except Exception as exc:
            log.warning("Fallback face detection falló: %s", exc)
        return (0, 0, 0, 0)

    # ------------------------------------------------------------------
    # Hair detection
    # ------------------------------------------------------------------

    def _detect_hair(
        self,
        img_bgr: np.ndarray,
        img_rgb: np.ndarray,
        face_bbox: tuple[int, int, int, int],
        w: int,
        h: int,
    ) -> BodyRegion | None:
        fx, fy, fw, fh = face_bbox
        if fw == 0:
            return None

        # La zona del cabello está sobre la frente, con un margen lateral
        hair_y0 = max(0, fy - int(fh * 0.6))
        hair_y1 = fy + int(fh * 0.15)
        hair_x0 = max(0, fx - int(fw * 0.3))
        hair_x1 = min(w, fx + fw + int(fw * 0.3))

        if hair_y1 <= hair_y0 or hair_x1 <= hair_x0:
            return None

        hair_crop = img_rgb[hair_y0:hair_y1, hair_x0:hair_x1]
        if hair_crop.size == 0:
            return None

        # Heurística: el cabello suele ser más oscuro que la piel
        hsv_crop = cv2.cvtColor(img_bgr[hair_y0:hair_y1, hair_x0:hair_x1], cv2.COLOR_BGR2HSV)
        lower_dark = np.array([0, 0, 0], dtype=np.uint8)
        upper_dark = np.array([180, 255, 120], dtype=np.uint8)
        mask = cv2.inRange(hsv_crop, lower_dark, upper_dark)
        dark_ratio = float(np.count_nonzero(mask)) / max(mask.size, 1)

        if dark_ratio < 0.15:
            return None

        return BodyRegion(
            type=BodyPartType.HAIR,
            bbox=(hair_x0, hair_y0, hair_x1 - hair_x0, hair_y1 - hair_y0),
            confidence=min(0.85, 0.3 + dark_ratio),
        )

    # ------------------------------------------------------------------
    # Body region estimation (proporciones)
    # ------------------------------------------------------------------

    def _estimate_body_regions(
        self,
        face_bbox: tuple[int, int, int, int],
        w: int, h: int,
    ) -> list[BodyRegion]:
        fx, fy, fw, fh = face_bbox
        if fw == 0 or fh == 0:
            return self._estimate_body_without_face(w, h)

        regions: list[BodyRegion] = []
        face_cx = fx + fw // 2
        body_width = int(fw * 3.2)  # ancho típico del torso ≈ 3× cara
        half_body = body_width // 2

        def _clamp_x(v: int) -> int:
            return max(0, min(w, v))

        def _clamp_y(v: int) -> int:
            return max(0, min(h, v))

        def _region(
            part: BodyPartType, x0: int, y0: int, x1: int, y1: int,
            conf: float = 0.60,
        ) -> BodyRegion:
            cx0 = _clamp_x(x0)
            cy0 = _clamp_y(y0)
            cx1 = _clamp_x(x1)
            cy1 = _clamp_y(y1)
            return BodyRegion(
                type=part,
                bbox=(cx0, cy0, max(0, cx1 - cx0), max(0, cy1 - cy0)),
                confidence=conf,
            )

        # Shoulders
        shoulder_y = fy + fh
        shoulder_h = int(fh * 0.12)
        shoulder_half_w = int(body_width * 0.55)
        regions.append(_region(
            BodyPartType.LEFT_SHOULDER,
            face_cx - shoulder_half_w, shoulder_y,
            face_cx, shoulder_y + shoulder_h,
        ))
        regions.append(_region(
            BodyPartType.RIGHT_SHOULDER,
            face_cx, shoulder_y,
            face_cx + shoulder_half_w, shoulder_y + shoulder_h,
        ))

        # Chest / Torso
        torso_top = shoulder_y + shoulder_h
        torso_h = int(h * 0.35)
        regions.append(_region(
            BodyPartType.CHEST,
            face_cx - half_body, torso_top,
            face_cx + half_body, torso_top + int(torso_h * 0.4),
        ))
        regions.append(_region(
            BodyPartType.TORSO,
            face_cx - half_body, torso_top + int(torso_h * 0.2),
            face_cx + half_body, torso_top + torso_h,
        ))

        # Hips
        hips_top = torso_top + torso_h
        hips_h = int(fh * 0.5)
        regions.append(_region(
            BodyPartType.HIPS,
            face_cx - int(half_body * 0.9), hips_top,
            face_cx + int(half_body * 0.9), hips_top + hips_h,
        ))

        # Arms
        arm_w = int(fw * 0.6)
        arm_top = shoulder_y
        arm_bottom = hips_top + int(hips_h * 0.8)
        regions.append(_region(
            BodyPartType.LEFT_ARM,
            face_cx - shoulder_half_w - arm_w, arm_top,
            face_cx - shoulder_half_w, arm_bottom,
        ))
        regions.append(_region(
            BodyPartType.RIGHT_ARM,
            face_cx + shoulder_half_w, arm_top,
            face_cx + shoulder_half_w + arm_w, arm_bottom,
        ))

        # Hands
        hand_size = int(fw * 0.55)
        regions.append(_region(
            BodyPartType.LEFT_HAND,
            face_cx - shoulder_half_w - arm_w - hand_size // 4,
            arm_bottom - hand_size // 2,
            face_cx - shoulder_half_w - arm_w + hand_size,
            arm_bottom + hand_size // 2,
            conf=0.45,
        ))
        regions.append(_region(
            BodyPartType.RIGHT_HAND,
            face_cx + shoulder_half_w + arm_w - hand_size,
            arm_bottom - hand_size // 2,
            face_cx + shoulder_half_w + arm_w + hand_size // 4,
            arm_bottom + hand_size // 2,
            conf=0.45,
        ))

        # Legs
        leg_top = hips_top + hips_h
        leg_h = h - leg_top
        leg_half_w = int(half_body * 0.4)
        regions.append(_region(
            BodyPartType.LEFT_LEG,
            face_cx - int(half_body * 0.7), leg_top,
            face_cx - int(half_body * 0.1), h,
        ))
        regions.append(_region(
            BodyPartType.RIGHT_LEG,
            face_cx + int(half_body * 0.1), leg_top,
            face_cx + int(half_body * 0.7), h,
        ))

        # Feet
        foot_h = int(leg_h * 0.15)
        foot_w = int(fw * 0.7)
        regions.append(_region(
            BodyPartType.LEFT_FOOT,
            face_cx - int(half_body * 0.7), h - foot_h,
            face_cx - int(half_body * 0.1) + foot_w, h,
            conf=0.40,
        ))
        regions.append(_region(
            BodyPartType.RIGHT_FOOT,
            face_cx + int(half_body * 0.1) - foot_w, h - foot_h,
            face_cx + int(half_body * 0.7), h,
            conf=0.40,
        ))

        # Neck
        neck_top = fy + fh
        neck_h = shoulder_h
        neck_half_w = int(fw * 0.4)
        regions.append(_region(
            BodyPartType.NECK,
            face_cx - neck_half_w, neck_top,
            face_cx + neck_half_w, neck_top + neck_h,
            conf=0.85,
        ))

        return regions

    def _estimate_body_without_face(self, w: int, h: int) -> list[BodyRegion]:
        """Estimaciones muy básicas cuando no se detectó cara."""
        cx = w // 2
        hw = w // 3
        return [
            BodyRegion(type=BodyPartType.TORSO, bbox=(cx - hw, int(h * 0.25), hw * 2, int(h * 0.35)), confidence=0.20),
            BodyRegion(type=BodyPartType.LEFT_ARM, bbox=(0, int(h * 0.28), cx - hw, int(h * 0.55)), confidence=0.15),
            BodyRegion(type=BodyPartType.RIGHT_ARM, bbox=(cx + hw, int(h * 0.28), w - cx - hw, int(h * 0.55)), confidence=0.15),
            BodyRegion(type=BodyPartType.LEFT_LEG, bbox=(cx - hw, int(h * 0.60), hw, int(h * 0.40)), confidence=0.15),
            BodyRegion(type=BodyPartType.RIGHT_LEG, bbox=(cx, int(h * 0.60), hw, int(h * 0.40)), confidence=0.15),
        ]

    # ------------------------------------------------------------------
    # Character type guess
    # ------------------------------------------------------------------

    @staticmethod
    def _guess_character_type(img_bgr: np.ndarray) -> str:
        """Heurística simple: compara regiones de color plano vs textura real."""
        small = cv2.resize(img_bgr, (128, 128))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(np.count_nonzero(edges)) / edges.size

        # Anime/Chibi → bordes más definidos, colores planos → menor varianza de color
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        saturation_std = float(hsv[:, :, 1].std())

        if edge_density > 0.08 and saturation_std < 50:
            return "anime"
        if edge_density > 0.12:
            return "realistic"
        if edge_density < 0.05:
            return "chibi"
        return "unknown"
