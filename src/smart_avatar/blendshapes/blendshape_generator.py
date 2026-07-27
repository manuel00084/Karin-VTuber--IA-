"""BlendShape generator — creates vertex-delta targets for facial expressions.

Every ``BlendShapeTarget`` maps a set of vertex indices to ``Vec3``
delta positions.  The magnitude of each delta is proportional to the
detected region size so that small and large avatars produce comparable
deformation intensities.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import numpy as np

from src.smart_avatar.core.interfaces import IBlendShapeGenerator
from src.smart_avatar.core.types import (
    BlendShapes,
    BlendShapeTarget,
    Mesh,
    MeshRegion,
    Skeleton,
    Vec2,
    Vec3,
    Vertex,
)


# ---------------------------------------------------------------------------
# Standard blendshape catalog
# ---------------------------------------------------------------------------

_EYE_SHAPES: List[str] = [
    "Blink_L", "Blink_R",
    "EyeLookUp_L", "EyeLookUp_R",
    "EyeLookDown_L", "EyeLookDown_R",
    "EyeLookLeft_L", "EyeLookLeft_R",
    "EyeLookRight_L", "EyeLookRight_R",
]

_MOUTH_SHAPES: List[str] = [
    "MouthA", "MouthE", "MouthI", "MouthO", "MouthU",
    "JawOpen", "JawClose",
]

_BROW_SHAPES: List[str] = [
    "BrowUp_L", "BrowUp_R",
    "BrowDown_L", "BrowDown_R",
]

_EMOTION_SHAPES: List[str] = [
    "Smile", "Sad", "Angry", "Surprise",
]

_ALL_SHAPES: List[str] = (
    _EYE_SHAPES + _MOUTH_SHAPES + _BROW_SHAPES + _EMOTION_SHAPES
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bbox_center(bbox: Tuple[int, int, int, int]) -> Vec2:
    x, y, w, h = bbox
    return Vec2(x + w / 2.0, y + h / 2.0)


def _bbox_size(bbox: Tuple[int, int, int, int]) -> Vec2:
    return Vec2(float(bbox[2]), float(bbox[3]))


def _vertices_in_region(
    region: MeshRegion, index_offset: int = 0
) -> List[int]:
    """Return global vertex indices for all vertices in *region*."""
    return [index_offset + i for i in range(len(region.vertices))]


class BlendShapeGenerator(IBlendShapeGenerator):
    """Generates standard blendshape targets as vertex-delta maps.

    Deltas are computed relative to the mesh region that each shape
    targets.  The scale of every delta is normalised by the region's
    bounding-box dimensions so that deformation feels consistent
    regardless of avatar proportions.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, mesh: Mesh, skeleton: Skeleton) -> BlendShapes:
        """Return a :class:`BlendShapes` containing every standard target.

        Parameters
        ----------
        mesh:
            Avatar mesh whose regions supply the vertex pools.
        skeleton:
            2-D controller skeleton (used for positional reference).
        """
        region_offsets = self._compute_region_offsets(mesh)
        scale = self._global_scale(mesh)

        shapes: Dict[str, BlendShapeTarget] = {}

        self._generate_eye_shapes(mesh, region_offsets, scale, shapes)
        self._generate_mouth_shapes(mesh, region_offsets, scale, shapes)
        self._generate_brow_shapes(mesh, region_offsets, scale, shapes)
        self._generate_emotion_shapes(mesh, region_offsets, scale, shapes)

        return BlendShapes(targets=shapes)

    # ------------------------------------------------------------------
    # Internals — utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_region_offsets(mesh: Mesh) -> Dict[str, int]:
        """Map region name → starting vertex index inside the flat list."""
        offsets: Dict[str, int] = {}
        cursor = 0
        for name, region in mesh.regions.items():
            offsets[name] = cursor
            cursor += len(region.vertices)
        return offsets

    @staticmethod
    def _global_scale(mesh: Mesh) -> float:
        """Approximate avatar scale factor based on average region width.

        A larger mesh produces proportionally larger deltas so that
        blendshapes look correct at any size.
        """
        widths: List[float] = []
        for region in mesh.regions.values():
            if not region.vertices:
                continue
            xs = [v.position.x for v in region.vertices]
            widths.append(max(xs) - min(xs) if len(xs) > 1 else 1.0)
        return (sum(widths) / len(widths)) if widths else 1.0

    @staticmethod
    def _make_target(
        name: str, deltas: List[Tuple[int, Vec3]]
    ) -> BlendShapeTarget:
        return BlendShapeTarget(name=name, vertex_deltas=deltas)

    @staticmethod
    def _region_vertices(
        mesh: Mesh, region_name: str, offsets: Dict[str, int]
    ) -> List[int]:
        region = mesh.regions.get(region_name)
        if region is None:
            return []
        offset = offsets.get(region_name, 0)
        return [offset + i for i in range(len(region.vertices))]

    # ------------------------------------------------------------------
    # Eye shapes
    # ------------------------------------------------------------------

    def _generate_eye_shapes(
        self,
        mesh: Mesh,
        offsets: Dict[str, int],
        scale: float,
        shapes: Dict[str, BlendShapeTarget],
    ) -> None:
        """Generate blink, gaze-up/down/left/right for both eyes."""
        left_verts = self._region_vertices(mesh, "left_eye", offsets)
        right_verts = self._region_vertices(mesh, "right_eye", offsets)

        blink_amount = scale * 0.08
        look_amount = scale * 0.05

        # Blink_L — compress vertically (Y → 0)
        shapes["Blink_L"] = self._make_target(
            "Blink_L",
            self._vertical_compress(left_verts, mesh, offsets, blink_amount),
        )
        # Blink_R
        shapes["Blink_R"] = self._make_target(
            "Blink_R",
            self._vertical_compress(right_verts, mesh, offsets, blink_amount),
        )

        # Look Up — shift Y negative
        shapes["EyeLookUp_L"] = self._make_target(
            "EyeLookUp_L",
            self._shift(left_verts, mesh, offsets, dy=-look_amount),
        )
        shapes["EyeLookUp_R"] = self._make_target(
            "EyeLookUp_R",
            self._shift(right_verts, mesh, offsets, dy=-look_amount),
        )

        # Look Down — shift Y positive
        shapes["EyeLookDown_L"] = self._make_target(
            "EyeLookDown_L",
            self._shift(left_verts, mesh, offsets, dy=look_amount),
        )
        shapes["EyeLookDown_R"] = self._make_target(
            "EyeLookDown_R",
            self._shift(right_verts, mesh, offsets, dy=look_amount),
        )

        # Look Left — shift X negative
        shapes["EyeLookLeft_L"] = self._make_target(
            "EyeLookLeft_L",
            self._shift(left_verts, mesh, offsets, dx=-look_amount),
        )
        shapes["EyeLookLeft_R"] = self._make_target(
            "EyeLookLeft_R",
            self._shift(right_verts, mesh, offsets, dx=-look_amount),
        )

        # Look Right — shift X positive
        shapes["EyeLookRight_L"] = self._make_target(
            "EyeLookRight_L",
            self._shift(left_verts, mesh, offsets, dx=look_amount),
        )
        shapes["EyeLookRight_R"] = self._make_target(
            "EyeLookRight_R",
            self._shift(right_verts, mesh, offsets, dx=look_amount),
        )

    # ------------------------------------------------------------------
    # Mouth shapes
    # ------------------------------------------------------------------

    def _generate_mouth_shapes(
        self,
        mesh: Mesh,
        offsets: Dict[str, int],
        scale: float,
        shapes: Dict[str, BlendShapeTarget],
    ) -> None:
        """Generate vowel shapes (A/E/I/O/U) and jaw open/close."""
        mouth_verts = self._region_vertices(mesh, "mouth", offsets)

        vowel_amount = scale * 0.06
        jaw_amount = scale * 0.10

        # MouthA (ah) — stretch vertically, widen slightly
        shapes["MouthA"] = self._make_target(
            "MouthA",
            self._mouth_vowel(mouth_verts, mesh, offsets,
                              dy=vowel_amount, dx=vowel_amount * 0.3),
        )
        # MouthE (ee) — narrow horizontally, stretch vertically a bit
        shapes["MouthE"] = self._make_target(
            "MouthE",
            self._mouth_vowel(mouth_verts, mesh, offsets,
                              dy=vowel_amount * 0.6, dx=-vowel_amount * 0.4),
        )
        # MouthI (ih) — narrowest
        shapes["MouthI"] = self._make_target(
            "MouthI",
            self._mouth_vowel(mouth_verts, mesh, offsets,
                              dy=vowel_amount * 0.4, dx=-vowel_amount * 0.6),
        )
        # MouthO (oh) — round, expand both axes
        shapes["MouthO"] = self._make_target(
            "MouthO",
            self._mouth_vowel(mouth_verts, mesh, offsets,
                              dy=vowel_amount * 0.7, dx=vowel_amount * 0.7),
        )
        # MouthU (oo) — small round, push forward (scale up uniformly)
        shapes["MouthU"] = self._make_target(
            "MouthU",
            self._mouth_vowel(mouth_verts, mesh, offsets,
                              dy=-vowel_amount * 0.3, dx=vowel_amount * 0.5),
        )

        # JawOpen — shift all mouth verts downward
        shapes["JawOpen"] = self._make_target(
            "JawOpen",
            self._shift(mouth_verts, mesh, offsets, dy=jaw_amount),
        )
        # JawClose — shift all mouth verts upward
        shapes["JawClose"] = self._make_target(
            "JawClose",
            self._shift(mouth_verts, mesh, offsets, dy=-jaw_amount),
        )

    # ------------------------------------------------------------------
    # Brow shapes
    # ------------------------------------------------------------------

    def _generate_brow_shapes(
        self,
        mesh: Mesh,
        offsets: Dict[str, int],
        scale: float,
        shapes: Dict[str, BlendShapeTarget],
    ) -> None:
        """Generate brow raise and furrow for both sides."""
        left_verts = self._region_vertices(mesh, "left_eyebrow", offsets)
        right_verts = self._region_vertices(mesh, "right_eyebrow", offsets)

        raise_amount = scale * 0.06
        furrow_amount = scale * 0.04

        # BrowUp — shift Y negative (screen-up)
        shapes["BrowUp_L"] = self._make_target(
            "BrowUp_L",
            self._shift(left_verts, mesh, offsets, dy=-raise_amount),
        )
        shapes["BrowUp_R"] = self._make_target(
            "BrowUp_R",
            self._shift(right_verts, mesh, offsets, dy=-raise_amount),
        )

        # BrowDown — shift Y positive (screen-down)
        shapes["BrowDown_L"] = self._make_target(
            "BrowDown_L",
            self._shift(left_verts, mesh, offsets, dy=furrow_amount),
        )
        shapes["BrowDown_R"] = self._make_target(
            "BrowDown_R",
            self._shift(right_verts, mesh, offsets, dy=furrow_amount),
        )

    # ------------------------------------------------------------------
    # Emotion shapes (compound)
    # ------------------------------------------------------------------

    def _generate_emotion_shapes(
        self,
        mesh: Mesh,
        offsets: Dict[str, int],
        scale: float,
        shapes: Dict[str, BlendShapeTarget],
    ) -> None:
        """Generate compound emotion blendshapes from region combos."""
        mouth_verts = self._region_vertices(mesh, "mouth", offsets)
        left_brow = self._region_vertices(mesh, "left_eyebrow", offsets)
        right_brow = self._region_vertices(mesh, "right_eyebrow", offsets)
        left_eye = self._region_vertices(mesh, "left_eye", offsets)
        right_eye = self._region_vertices(mesh, "right_eye", offsets)

        smile_amt = scale * 0.07
        sad_amt = scale * 0.05
        angry_amt = scale * 0.05
        surprise_amt = scale * 0.09

        # Smile — mouth corners up + eyes slightly narrow
        smile_deltas: List[Tuple[int, Vec3]] = []
        smile_deltas.extend(
            self._mouth_vowel(mouth_verts, mesh, offsets,
                              dy=-smile_amt * 0.5, dx=smile_amt * 0.4)
        )
        smile_deltas.extend(
            self._vertical_compress(left_eye, mesh, offsets,
                                    smile_amt * 0.3)
        )
        smile_deltas.extend(
            self._vertical_compress(right_eye, mesh, offsets,
                                    smile_amt * 0.3)
        )
        shapes["Smile"] = self._make_target("Smile", smile_deltas)

        # Sad — mouth corners down + brows down
        sad_deltas: List[Tuple[int, Vec3]] = []
        sad_deltas.extend(
            self._mouth_vowel(mouth_verts, mesh, offsets,
                              dy=sad_amt * 0.5, dx=-sad_amt * 0.2)
        )
        sad_deltas.extend(
            self._shift(left_brow, mesh, offsets, dy=sad_amt)
        )
        sad_deltas.extend(
            self._shift(right_brow, mesh, offsets, dy=sad_amt)
        )
        sad_deltas.extend(
            self._shift(left_eye, mesh, offsets, dy=sad_amt * 0.3)
        )
        sad_deltas.extend(
            self._shift(right_eye, mesh, offsets, dy=sad_amt * 0.3)
        )
        shapes["Sad"] = self._make_target("Sad", sad_deltas)

        # Angry — brows down + furrowed + mouth tight
        angry_deltas: List[Tuple[int, Vec3]] = []
        angry_deltas.extend(
            self._shift(left_brow, mesh, offsets,
                        dy=angry_amt, dx=angry_amt * 0.3)
        )
        angry_deltas.extend(
            self._shift(right_brow, mesh, offsets,
                        dy=angry_amt, dx=-angry_amt * 0.3)
        )
        angry_deltas.extend(
            self._mouth_vowel(mouth_verts, mesh, offsets,
                              dy=-angry_amt * 0.3, dx=-angry_amt * 0.5)
        )
        angry_deltas.extend(
            self._vertical_compress(left_eye, mesh, offsets,
                                    angry_amt * 0.4)
        )
        angry_deltas.extend(
            self._vertical_compress(right_eye, mesh, offsets,
                                    angry_amt * 0.4)
        )
        shapes["Angry"] = self._make_target("Angry", angry_deltas)

        # Surprise — brows up + eyes wide + mouth open
        surp_deltas: List[Tuple[int, Vec3]] = []
        surp_deltas.extend(
            self._shift(left_brow, mesh, offsets, dy=-surprise_amt)
        )
        surp_deltas.extend(
            self._shift(right_brow, mesh, offsets, dy=-surprise_amt)
        )
        surp_deltas.extend(
            self._shift(left_eye, mesh, offsets, dy=-surprise_amt * 0.3)
        )
        surp_deltas.extend(
            self._shift(right_eye, mesh, offsets, dy=-surprise_amt * 0.3)
        )
        surp_deltas.extend(
            self._mouth_vowel(mouth_verts, mesh, offsets,
                              dy=surprise_amt * 0.6, dx=surprise_amt * 0.3)
        )
        shapes["Surprise"] = self._make_target("Surprise", surp_deltas)

    # ------------------------------------------------------------------
    # Low-level vertex displacement helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _shift(
        vert_indices: List[int],
        mesh: Mesh,
        offsets: Dict[str, int],
        dx: float = 0.0,
        dy: float = 0.0,
    ) -> List[Tuple[int, Vec3]]:
        """Translate all listed vertices by (dx, dy)."""
        return [(idx, Vec3(dx, dy, 0.0)) for idx in vert_indices]

    @staticmethod
    def _vertical_compress(
        vert_indices: List[int],
        mesh: Mesh,
        offsets: Dict[str, int],
        amount: float,
    ) -> List[Tuple[int, Vec3]]:
        """Move vertices toward the region's vertical centre by *amount*.

        Vertices above the centre move down, vertices below move up,
        producing a squint / blink effect.
        """
        # Find the Y range of the referenced vertices.
        all_verts: List[Vertex] = []
        for region in mesh.regions.values():
            all_verts.extend(region.vertices)
        if not all_verts:
            return [(idx, Vec3(0.0, -amount, 0.0)) for idx in vert_indices]

        # Compute average Y of the target vertices.
        ys = []
        for idx in vert_indices:
            if 0 <= idx < len(all_verts):
                ys.append(all_verts[idx].position.y)
        if not ys:
            return [(idx, Vec3(0.0, -amount, 0.0)) for idx in vert_indices]

        center_y = sum(ys) / len(ys)

        deltas: List[Tuple[int, Vec3]] = []
        for idx in vert_indices:
            if 0 <= idx < len(all_verts):
                vy = all_verts[idx].position.y
                direction = -1.0 if vy > center_y else 1.0
                deltas.append((idx, Vec3(0.0, direction * amount, 0.0)))
            else:
                deltas.append((idx, Vec3(0.0, -amount, 0.0)))
        return deltas

    @staticmethod
    def _mouth_vowel(
        vert_indices: List[int],
        mesh: Mesh,
        offsets: Dict[str, int],
        dx: float = 0.0,
        dy: float = 0.0,
    ) -> List[Tuple[int, Vec3]]:
        """Displace mouth vertices radially from the mouth centre.

        Vertices farther from the centre receive larger deltas, creating
        a natural-looking vowel deformation rather than a uniform shift.
        """
        all_verts: List[Vertex] = []
        for region in mesh.regions.values():
            all_verts.extend(region.vertices)
        if not all_verts:
            return [(idx, Vec3(dx, dy, 0.0)) for idx in vert_indices]

        # Compute mouth centre.
        xs, ys = [], []
        for idx in vert_indices:
            if 0 <= idx < len(all_verts):
                xs.append(all_verts[idx].position.x)
                ys.append(all_verts[idx].position.y)
        if not xs:
            return [(idx, Vec3(dx, dy, 0.0)) for idx in vert_indices]

        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        max_dist = max(
            math.sqrt((all_verts[i].position.x - cx) ** 2
                      + (all_verts[i].position.y - cy) ** 2)
            for i in vert_indices
            if 0 <= i < len(all_verts)
        ) or 1.0

        deltas: List[Tuple[int, Vec3]] = []
        for idx in vert_indices:
            if 0 <= idx < len(all_verts):
                vx = all_verts[idx].position.x
                vy = all_verts[idx].position.y
                dist = math.sqrt((vx - cx) ** 2 + (vy - cy) ** 2)
                factor = 0.5 + 0.5 * (dist / max_dist)
                deltas.append((idx, Vec3(dx * factor, dy * factor, 0.0)))
            else:
                deltas.append((idx, Vec3(dx, dy, 0.0)))
        return deltas
